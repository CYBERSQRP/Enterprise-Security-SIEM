use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Event {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub source: String,
    pub event_type: String,
    pub severity: Severity,
    pub data: HashMap<String, serde_json::Value>,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum Severity {
    Low = 1,
    Medium = 2,
    High = 3,
    Critical = 4,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationRule {
    pub id: String,
    pub name: String,
    pub description: String,
    pub enabled: bool,
    pub rule_type: RuleType,
    pub conditions: Vec<Condition>,
    pub actions: Vec<Action>,
    pub severity: Severity,
    pub tags: Vec<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum RuleType {
    Threshold {
        count: u32,
        timewindow_seconds: u64,
        field: String,
    },
    Sequence {
        events: Vec<EventPattern>,
        max_span_seconds: u64,
    },
    Statistical {
        field: String,
        threshold_std_dev: f64,
        baseline_window_seconds: u64,
    },
    Correlation {
        event_types: Vec<String>,
        correlation_field: String,
        timewindow_seconds: u64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventPattern {
    pub event_type: String,
    pub conditions: Vec<Condition>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Condition {
    pub field: String,
    pub operator: Operator,
    pub value: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Operator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    Contains,
    Matches, // Regex
    In,
    NotIn,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Action {
    CreateAlert {
        title: String,
        description: String,
    },
    SendNotification {
        channel: String,
        template: String,
    },
    ExecutePlaybook {
        playbook_id: String,
    },
    EnrichEvent {
        enrichment_type: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorrelationResult {
    pub id: Uuid,
    pub rule_id: String,
    pub rule_name: String,
    pub matched_events: Vec<String>,
    pub severity: Severity,
    pub triggered_at: DateTime<Utc>,
    pub actions_executed: Vec<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub id: Uuid,
    pub correlation_id: Option<Uuid>,
    pub title: String,
    pub description: String,
    pub severity: Severity,
    pub status: AlertStatus,
    pub source_events: Vec<String>,
    pub assigned_to: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub resolved_at: Option<DateTime<Utc>>,
    pub tags: Vec<String>,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AlertStatus {
    New,
    Acknowledged,
    InProgress,
    Resolved,
    FalsePositive,
}
