package config

import (
	"os"
	"strconv"
)

type Config struct {
	Server        ServerConfig
	Database      DatabaseConfig
	Redis         RedisConfig
	Kafka         KafkaConfig
	Notifications NotificationConfig
}

type ServerConfig struct {
	Host string
	Port int
}

type DatabaseConfig struct {
	URL string
}

type RedisConfig struct {
	URL string
}

type KafkaConfig struct {
	Brokers []string
	Topic   string
	GroupID string
}

type NotificationConfig struct {
	EmailEnabled  bool
	SlackWebhook  string
	TeamsWebhook  string
	SMTPHost      string
	SMTPPort      int
	SMTPUser      string
	SMTPPassword  string
}

func Load() (*Config, error) {
	cfg := &Config{
		Server: ServerConfig{
			Host: getEnv("SERVER_HOST", "0.0.0.0"),
			Port: getEnvInt("SERVER_PORT", 8081),
		},
		Database: DatabaseConfig{
			URL: getEnv("DATABASE_URL", "postgresql://siem:siem@postgres:5432/siem"),
		},
		Redis: RedisConfig{
			URL: getEnv("REDIS_URL", "redis://redis:6379"),
		},
		Kafka: KafkaConfig{
			Brokers: []string{getEnv("KAFKA_BROKERS", "kafka:9092")},
			Topic:   getEnv("KAFKA_TOPIC", "alerts"),
			GroupID: getEnv("KAFKA_GROUP_ID", "alert-manager"),
		},
		Notifications: NotificationConfig{
			EmailEnabled:  getEnvBool("NOTIFICATIONS_EMAIL_ENABLED", false),
			SlackWebhook:  getEnv("SLACK_WEBHOOK_URL", ""),
			TeamsWebhook:  getEnv("TEAMS_WEBHOOK_URL", ""),
			SMTPHost:      getEnv("SMTP_HOST", ""),
			SMTPPort:      getEnvInt("SMTP_PORT", 587),
			SMTPUser:      getEnv("SMTP_USER", ""),
			SMTPPassword:  getEnv("SMTP_PASSWORD", ""),
		},
	}

	return cfg, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolVal, err := strconv.ParseBool(value); err == nil {
			return boolVal
		}
	}
	return defaultValue
}
