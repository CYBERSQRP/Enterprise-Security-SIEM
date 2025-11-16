use crate::config::Config;
use crate::models::*;
use anyhow::{Result, Context};
use redis::AsyncCommands;
use sqlx::{PgPool, postgres::PgPoolOptions};
use std::sync::Arc;

pub struct Storage {
    db_pool: PgPool,
    redis_client: redis::Client,
}

impl Storage {
    pub async fn new(config: &Config) -> Result<Self> {
        // Initialize PostgreSQL connection pool
        let db_pool = PgPoolOptions::new()
            .max_connections(10)
            .connect(&config.database.url)
            .await
            .context("Failed to connect to PostgreSQL")?;

        // Initialize Redis client
        let redis_client = redis::Client::open(config.redis.url.as_str())
            .context("Failed to create Redis client")?;

        Ok(Self {
            db_pool,
            redis_client,
        })
    }

    pub async fn store_event(&self, event: &Event) -> Result<()> {
        // In production, this would batch insert events
        Ok(())
    }

    pub async fn store_correlation(&self, result: &CorrelationResult) -> Result<()> {
        sqlx::query!(
            r#"
            INSERT INTO correlations (id, rule_id, rule_name, severity, triggered_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6)
            "#,
            result.id,
            result.rule_id,
            result.rule_name,
            result.severity as i32,
            result.triggered_at,
            serde_json::to_value(&result.metadata)?
        )
        .execute(&self.db_pool)
        .await
        .context("Failed to store correlation result")?;

        Ok(())
    }

    pub async fn load_rules(&self) -> Result<Vec<CorrelationRule>> {
        let rows = sqlx::query!(
            r#"
            SELECT id, name, description, enabled, rule_type, conditions, actions, severity, tags, created_at, updated_at
            FROM correlation_rules
            WHERE enabled = true
            "#
        )
        .fetch_all(&self.db_pool)
        .await
        .context("Failed to load correlation rules")?;

        let mut rules = Vec::new();
        for row in rows {
            // Parse rule from database - simplified for now
            // In production, properly deserialize from JSON columns
        }

        Ok(rules)
    }

    pub async fn get_event_count(&self) -> Result<u64> {
        Ok(0) // Placeholder
    }

    pub async fn get_correlation_count(&self) -> Result<u64> {
        let result = sqlx::query!("SELECT COUNT(*) as count FROM correlations")
            .fetch_one(&self.db_pool)
            .await?;

        Ok(result.count.unwrap_or(0) as u64)
    }
}
