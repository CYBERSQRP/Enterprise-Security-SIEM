use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    pub server: ServerConfig,
    pub kafka: KafkaConfig,
    pub redis: RedisConfig,
    pub database: DatabaseConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Clone, Deserialize)]
pub struct KafkaConfig {
    pub brokers: String,
    pub input_topic: String,
    pub output_topic: String,
    pub group_id: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RedisConfig {
    pub url: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
}

impl Config {
    pub fn from_env() -> Result<Self, config::ConfigError> {
        let settings = config::Config::builder()
            .set_default("server.host", "0.0.0.0")?
            .set_default("server.port", 8080)?
            .set_default("kafka.brokers", "kafka:9092")?
            .set_default("kafka.input_topic", "events")?
            .set_default("kafka.output_topic", "alerts")?
            .set_default("kafka.group_id", "correlation-engine")?
            .set_default("redis.url", "redis://redis:6379")?
            .set_default("database.url", "postgresql://siem:siem@postgres:5432/siem")?
            .add_source(
                config::Environment::with_prefix("CORRELATOR")
                    .separator("_")
            )
            .build()?;

        settings.try_deserialize()
    }
}
