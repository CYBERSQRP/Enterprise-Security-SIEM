use crate::models::*;
use crate::storage::Storage;
use anyhow::{Result, anyhow};
use chrono::{Utc, Duration};
use dashmap::DashMap;
use log::{info, debug};
use regex::Regex;
use std::sync::Arc;
use uuid::Uuid;

pub struct RuleEngine {
    storage: Arc<Storage>,
    active_rules: Arc<DashMap<String, CorrelationRule>>,
}

impl RuleEngine {
    pub async fn new(storage: Arc<Storage>) -> Result<Self> {
        let engine = Self {
            storage,
            active_rules: Arc::new(DashMap::new()),
        };

        engine.reload_rules().await?;
        Ok(engine)
    }

    pub async fn reload_rules(&self) -> Result<()> {
        info!("Loading correlation rules from storage");

        let rules = self.storage.load_rules().await?;
        self.active_rules.clear();

        for rule in rules {
            if rule.enabled {
                self.active_rules.insert(rule.id.clone(), rule);
            }
        }

        info!("Loaded {} active correlation rules", self.active_rules.len());
        Ok(())
    }

    pub async fn evaluate(
        &self,
        event: &Event,
        correlation_windows: &Arc<DashMap<String, Vec<Event>>>,
    ) -> Result<Vec<CorrelationResult>> {
        let mut results = Vec::new();

        for rule_entry in self.active_rules.iter() {
            let rule = rule_entry.value();

            if let Some(result) = self.evaluate_rule(rule, event, correlation_windows).await? {
                results.push(result);
            }
        }

        Ok(results)
    }

    async fn evaluate_rule(
        &self,
        rule: &CorrelationRule,
        event: &Event,
        correlation_windows: &Arc<DashMap<String, Vec<Event>>>,
    ) -> Result<Option<CorrelationResult>> {
        debug!("Evaluating rule: {}", rule.name);

        // Check if event matches rule conditions
        if !self.matches_conditions(event, &rule.conditions) {
            return Ok(None);
        }

        match &rule.rule_type {
            RuleType::Threshold { count, timewindow_seconds, field } => {
                self.evaluate_threshold_rule(rule, event, *count, *timewindow_seconds, field, correlation_windows).await
            }
            RuleType::Sequence { events, max_span_seconds } => {
                self.evaluate_sequence_rule(rule, event, events, *max_span_seconds, correlation_windows).await
            }
            RuleType::Statistical { field, threshold_std_dev, baseline_window_seconds } => {
                self.evaluate_statistical_rule(rule, event, field, *threshold_std_dev, *baseline_window_seconds).await
            }
            RuleType::Correlation { event_types, correlation_field, timewindow_seconds } => {
                self.evaluate_correlation_rule(rule, event, event_types, correlation_field, *timewindow_seconds, correlation_windows).await
            }
        }
    }

    fn matches_conditions(&self, event: &Event, conditions: &[Condition]) -> bool {
        for condition in conditions {
            if !self.matches_condition(event, condition) {
                return false;
            }
        }
        true
    }

    fn matches_condition(&self, event: &Event, condition: &Condition) -> bool {
        let field_value = event.data.get(&condition.field);

        match (&condition.operator, field_value) {
            (Operator::Equals, Some(value)) => value == &condition.value,
            (Operator::NotEquals, Some(value)) => value != &condition.value,
            (Operator::GreaterThan, Some(value)) => {
                if let (Some(v1), Some(v2)) = (value.as_f64(), condition.value.as_f64()) {
                    v1 > v2
                } else {
                    false
                }
            }
            (Operator::LessThan, Some(value)) => {
                if let (Some(v1), Some(v2)) = (value.as_f64(), condition.value.as_f64()) {
                    v1 < v2
                } else {
                    false
                }
            }
            (Operator::Contains, Some(value)) => {
                if let (Some(haystack), Some(needle)) = (value.as_str(), condition.value.as_str()) {
                    haystack.contains(needle)
                } else {
                    false
                }
            }
            (Operator::Matches, Some(value)) => {
                if let (Some(text), Some(pattern)) = (value.as_str(), condition.value.as_str()) {
                    Regex::new(pattern).map(|re| re.is_match(text)).unwrap_or(false)
                } else {
                    false
                }
            }
            (Operator::In, Some(value)) => {
                if let Some(arr) = condition.value.as_array() {
                    arr.contains(value)
                } else {
                    false
                }
            }
            (Operator::NotIn, Some(value)) => {
                if let Some(arr) = condition.value.as_array() {
                    !arr.contains(value)
                } else {
                    false
                }
            }
            _ => false,
        }
    }

    async fn evaluate_threshold_rule(
        &self,
        rule: &CorrelationRule,
        event: &Event,
        count: u32,
        timewindow_seconds: u64,
        field: &str,
        correlation_windows: &Arc<DashMap<String, Vec<Event>>>,
    ) -> Result<Option<CorrelationResult>> {
        let window_key = format!("threshold_{}_{}", rule.id,
            event.data.get(field).map(|v| v.to_string()).unwrap_or_default());

        // Add event to correlation window
        correlation_windows
            .entry(window_key.clone())
            .or_insert_with(Vec::new)
            .push(event.clone());

        // Clean old events from window
        let cutoff_time = Utc::now() - Duration::seconds(timewindow_seconds as i64);
        if let Some(mut window) = correlation_windows.get_mut(&window_key) {
            window.retain(|e| e.timestamp > cutoff_time);

            // Check if threshold is met
            if window.len() >= count as usize {
                let matched_events: Vec<String> = window.iter().map(|e| e.id.clone()).collect();

                return Ok(Some(CorrelationResult {
                    id: Uuid::new_v4(),
                    rule_id: rule.id.clone(),
                    rule_name: rule.name.clone(),
                    matched_events,
                    severity: rule.severity,
                    triggered_at: Utc::now(),
                    actions_executed: rule.actions.iter().map(|a| format!("{:?}", a)).collect(),
                    metadata: std::collections::HashMap::new(),
                }));
            }
        }

        Ok(None)
    }

    async fn evaluate_sequence_rule(
        &self,
        rule: &CorrelationRule,
        event: &Event,
        patterns: &[EventPattern],
        max_span_seconds: u64,
        correlation_windows: &Arc<DashMap<String, Vec<Event>>>,
    ) -> Result<Option<CorrelationResult>> {
        // Simplified sequence detection - would need more sophisticated implementation
        Ok(None)
    }

    async fn evaluate_statistical_rule(
        &self,
        rule: &CorrelationRule,
        event: &Event,
        field: &str,
        threshold_std_dev: f64,
        baseline_window_seconds: u64,
    ) -> Result<Option<CorrelationResult>> {
        // Simplified statistical anomaly detection - would need historical baseline
        Ok(None)
    }

    async fn evaluate_correlation_rule(
        &self,
        rule: &CorrelationRule,
        event: &Event,
        event_types: &[String],
        correlation_field: &str,
        timewindow_seconds: u64,
        correlation_windows: &Arc<DashMap<String, Vec<Event>>>,
    ) -> Result<Option<CorrelationResult>> {
        // Simplified correlation - would need more sophisticated implementation
        Ok(None)
    }

    pub fn get_active_rule_count(&self) -> usize {
        self.active_rules.len()
    }
}
