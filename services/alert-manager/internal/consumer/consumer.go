package consumer

import (
	"context"
	"encoding/json"
	"time"

	"github.com/enterprise-siem/alert-manager/internal/config"
	"github.com/enterprise-siem/alert-manager/internal/models"
	"github.com/enterprise-siem/alert-manager/internal/notification"
	"github.com/enterprise-siem/alert-manager/internal/storage"
	"github.com/google/uuid"
	"github.com/segmentio/kafka-go"
	log "github.com/sirupsen/logrus"
)

type Consumer struct {
	reader   *kafka.Reader
	store    *storage.Storage
	notifier *notification.Service
}

func New(cfg config.KafkaConfig, store *storage.Storage, notifier *notification.Service) *Consumer {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:  cfg.Brokers,
		Topic:    cfg.Topic,
		GroupID:  cfg.GroupID,
		MinBytes: 10e3, // 10KB
		MaxBytes: 10e6, // 10MB
	})

	return &Consumer{
		reader:   reader,
		store:    store,
		notifier: notifier,
	}
}

func (c *Consumer) Start(ctx context.Context) error {
	log.Info("Starting Kafka consumer")

	for {
		select {
		case <-ctx.Done():
			log.Info("Stopping Kafka consumer")
			return c.reader.Close()
		default:
			msg, err := c.reader.ReadMessage(ctx)
			if err != nil {
				log.Errorf("Error reading message: %v", err)
				continue
			}

			if err := c.processMessage(ctx, msg); err != nil {
				log.Errorf("Error processing message: %v", err)
			}
		}
	}
}

func (c *Consumer) processMessage(ctx context.Context, msg kafka.Message) error {
	log.WithField("partition", msg.Partition).
		WithField("offset", msg.Offset).
		Debug("Processing message")

	var correlationResult map[string]interface{}
	if err := json.Unmarshal(msg.Value, &correlationResult); err != nil {
		return err
	}

	// Convert correlation result to alert
	alert := &models.Alert{
		ID:          uuid.New(),
		Title:       fmt.Sprintf("%v", correlationResult["rule_name"]),
		Description: fmt.Sprintf("Correlation detected: %v", correlationResult["rule_name"]),
		Severity:    models.SeverityHigh, // Would be derived from correlation
		Status:      models.StatusNew,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
		Tags:        []string{"correlation"},
		Metadata:    correlationResult,
	}

	// Store alert
	if err := c.store.CreateAlert(ctx, alert); err != nil {
		return err
	}

	// Send notifications
	go c.notifier.NotifyAlert(alert)

	log.WithField("alert_id", alert.ID).Info("Alert created from correlation")
	return nil
}

func (c *Consumer) Close() error {
	return c.reader.Close()
}
