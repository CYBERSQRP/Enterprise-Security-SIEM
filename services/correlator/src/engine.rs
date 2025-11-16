use crate::config::Config;
use crate::models::*;
use crate::rules::RuleEngine;
use crate::storage::Storage;
use anyhow::{Result, Context};
use chrono::Utc;
use dashmap::DashMap;
use log::{info, warn, error, debug};
use rdkafka::consumer::{StreamConsumer, Consumer};
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::{ClientConfig, Message};
use std::sync::Arc;
use std::time::Duration;
use uuid::Uuid;

pub struct CorrelationEngine {
    config: Config,
    rule_engine: Arc<RuleEngine>,
    storage: Arc<Storage>,
    consumer: StreamConsumer,
    producer: FutureProducer,
    // In-memory correlation state
    correlation_windows: Arc<DashMap<String, Vec<Event>>>,
}

impl CorrelationEngine {
    pub async fn new(config: Config) -> Result<Self> {
        info!("Initializing Correlation Engine");

        // Initialize Kafka consumer
        let consumer: StreamConsumer = ClientConfig::new()
            .set("group.id", &config.kafka.group_id)
            .set("bootstrap.servers", &config.kafka.brokers)
            .set("enable.partition.eof", "false")
            .set("session.timeout.ms", "6000")
            .set("enable.auto.commit", "true")
            .create()
            .context("Failed to create Kafka consumer")?;

        consumer
            .subscribe(&[&config.kafka.input_topic])
            .context("Failed to subscribe to Kafka topic")?;

        // Initialize Kafka producer
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", &config.kafka.brokers)
            .set("message.timeout.ms", "5000")
            .create()
            .context("Failed to create Kafka producer")?;

        // Initialize storage
        let storage = Arc::new(Storage::new(&config).await?);

        // Initialize rule engine
        let rule_engine = Arc::new(RuleEngine::new(storage.clone()).await?);

        Ok(Self {
            config,
            rule_engine,
            storage,
            consumer,
            producer,
            correlation_windows: Arc::new(DashMap::new()),
        })
    }

    pub async fn start(&self) -> Result<()> {
        info!("Starting correlation engine event processing");

        use rdkafka::message::BorrowedMessage;
        use futures::StreamExt;

        let mut message_stream = self.consumer.stream();

        while let Some(message) = message_stream.next().await {
            match message {
                Ok(borrowed_message) => {
                    if let Err(e) = self.process_message(&borrowed_message).await {
                        error!("Error processing message: {}", e);
                    }
                }
                Err(e) => {
                    error!("Kafka error: {}", e);
                }
            }
        }

        Ok(())
    }

    async fn process_message(&self, message: &rdkafka::message::BorrowedMessage<'_>) -> Result<()> {
        let payload = match message.payload() {
            Some(p) => p,
            None => {
                warn!("Received empty message");
                return Ok(());
            }
        };

        let event: Event = serde_json::from_slice(payload)
            .context("Failed to deserialize event")?;

        debug!("Processing event: {} ({})", event.id, event.event_type);

        // Store event
        self.storage.store_event(&event).await?;

        // Evaluate event against all active rules
        let results = self.rule_engine.evaluate(&event, &self.correlation_windows).await?;

        // Process correlation results
        for result in results {
            self.handle_correlation_result(result).await?;
        }

        Ok(())
    }

    async fn handle_correlation_result(&self, result: CorrelationResult) -> Result<()> {
        info!(
            "Correlation match: {} (rule: {})",
            result.id, result.rule_name
        );

        // Store correlation result
        self.storage.store_correlation(&result).await?;

        // Execute actions
        for action in &result.actions_executed {
            debug!("Executing action: {}", action);
        }

        // Publish alert to Kafka
        let alert_json = serde_json::to_string(&result)?;
        let record = FutureRecord::to(&self.config.kafka.output_topic)
            .payload(&alert_json)
            .key(&result.rule_id);

        match self.producer.send(record, Duration::from_secs(0)).await {
            Ok(_) => info!("Alert published for correlation {}", result.id),
            Err((e, _)) => error!("Failed to publish alert: {:?}", e),
        }

        Ok(())
    }

    pub async fn reload_rules(&self) -> Result<()> {
        info!("Reloading correlation rules");
        self.rule_engine.reload_rules().await
    }

    pub async fn get_stats(&self) -> Result<EngineStats> {
        Ok(EngineStats {
            active_rules: self.rule_engine.get_active_rule_count(),
            events_processed: self.storage.get_event_count().await?,
            correlations_triggered: self.storage.get_correlation_count().await?,
            correlation_windows_active: self.correlation_windows.len(),
        })
    }
}

#[derive(Debug, serde::Serialize)]
pub struct EngineStats {
    pub active_rules: usize,
    pub events_processed: u64,
    pub correlations_triggered: u64,
    pub correlation_windows_active: usize,
}
