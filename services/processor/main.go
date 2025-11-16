package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/enterprise-siem/platform/shared/models"
	"github.com/elastic/go-elasticsearch/v8"
)

type ProcessorService struct {
	kafkaConsumer *kafka.Consumer
	kafkaProducer *kafka.Producer
	esClient      *elasticsearch.Client
	config        *Config
}

type Config struct {
	KafkaBrokers      string
	InputTopic        string
	OutputTopic       string
	ConsumerGroup     string
	ElasticsearchURL  string
}

func main() {
	config := &Config{
		KafkaBrokers:     getEnv("KAFKA_BROKERS", "localhost:9092"),
		InputTopic:       getEnv("INPUT_TOPIC", "raw-events"),
		OutputTopic:      getEnv("OUTPUT_TOPIC", "normalized-events"),
		ConsumerGroup:    getEnv("CONSUMER_GROUP", "processor-group"),
		ElasticsearchURL: getEnv("ELASTICSEARCH_URL", "http://localhost:9200"),
	}

	service, err := NewProcessorService(config)
	if err != nil {
		log.Fatalf("Failed to create processor service: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		if err := service.Start(ctx); err != nil {
			log.Printf("Processor service error: %v", err)
		}
	}()

	log.Println("Processor service started")

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down processor service...")
	cancel()
	service.Close()
}

func NewProcessorService(config *Config) (*ProcessorService, error) {
	// Create Kafka consumer
	consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": config.KafkaBrokers,
		"group.id":          config.ConsumerGroup,
		"auto.offset.reset": "earliest",
	})
	if err != nil {
		return nil, err
	}

	// Create Kafka producer
	producer, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": config.KafkaBrokers,
		"client.id":         "siem-processor",
	})
	if err != nil {
		return nil, err
	}

	// Create Elasticsearch client
	esCfg := elasticsearch.Config{
		Addresses: []string{config.ElasticsearchURL},
	}
	esClient, err := elasticsearch.NewClient(esCfg)
	if err != nil {
		return nil, err
	}

	return &ProcessorService{
		kafkaConsumer: consumer,
		kafkaProducer: producer,
		esClient:      esClient,
		config:        config,
	}, nil
}

func (ps *ProcessorService) Start(ctx context.Context) error {
	// Subscribe to input topic
	err := ps.kafkaConsumer.Subscribe(ps.config.InputTopic, nil)
	if err != nil {
		return err
	}

	log.Printf("Subscribed to topic: %s", ps.config.InputTopic)

	for {
		select {
		case <-ctx.Done():
			return nil
		default:
			msg, err := ps.kafkaConsumer.ReadMessage(1 * time.Second)
			if err != nil {
				if err.(kafka.Error).Code() == kafka.ErrTimedOut {
					continue
				}
				log.Printf("Consumer error: %v", err)
				continue
			}

			// Process the event
			ps.processEvent(msg.Value)
		}
	}
}

func (ps *ProcessorService) processEvent(data []byte) {
	var event models.CommonEvent
	if err := json.Unmarshal(data, &event); err != nil {
		log.Printf("Failed to unmarshal event: %v", err)
		return
	}

	// Normalize the event
	ps.normalizeEvent(&event)

	// Enrich the event
	ps.enrichEvent(&event)

	// Index to Elasticsearch
	if err := ps.indexEvent(&event); err != nil {
		log.Printf("Failed to index event: %v", err)
	}

	// Send to output topic
	if err := ps.sendToKafka(&event); err != nil {
		log.Printf("Failed to send to Kafka: %v", err)
	}
}

func (ps *ProcessorService) normalizeEvent(event *models.CommonEvent) {
	// Normalize timestamp to UTC
	event.Timestamp = event.Timestamp.UTC()
	event.IngestionTime = time.Now().UTC()

	// Set default values if missing
	if event.Event.Severity == "" {
		event.Event.Severity = "info"
	}

	if event.Metadata.RetentionDays == 0 {
		event.Metadata.RetentionDays = 30
	}
}

func (ps *ProcessorService) enrichEvent(event *models.CommonEvent) {
	// Basic enrichment - in production, this would call external services
	if event.Enrichment == nil {
		event.Enrichment = &models.Enrichment{}
	}

	// GeoIP enrichment (simplified)
	if event.Source.IP != "" && event.Enrichment.GeoIP == nil {
		event.Enrichment.GeoIP = &models.GeoIPEnrichment{
			Country: "US",
			City:    "Unknown",
		}
	}

	// Asset enrichment (simplified)
	if event.Source.Hostname != "" && event.Enrichment.Asset == nil {
		event.Enrichment.Asset = &models.AssetEnrichment{
			Criticality: "medium",
			Tags:        []string{"server"},
		}
	}
}

func (ps *ProcessorService) indexEvent(event *models.CommonEvent) error {
	// Create index name based on date
	indexName := "events-" + event.Timestamp.Format("2006.01.02")

	eventJSON, err := json.Marshal(event)
	if err != nil {
		return err
	}

	// Index the document
	_, err = ps.esClient.Index(
		indexName,
		strings.NewReader(string(eventJSON)),
		ps.esClient.Index.WithDocumentID(event.EventID),
		ps.esClient.Index.WithRefresh("true"),
	)

	return err
}

func (ps *ProcessorService) sendToKafka(event *models.CommonEvent) error {
	eventJSON, err := json.Marshal(event)
	if err != nil {
		return err
	}

	topic := ps.config.OutputTopic
	return ps.kafkaProducer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
		Value:          eventJSON,
		Key:            []byte(event.EventID),
	}, nil)
}

func (ps *ProcessorService) Close() {
	if ps.kafkaConsumer != nil {
		ps.kafkaConsumer.Close()
	}
	if ps.kafkaProducer != nil {
		ps.kafkaProducer.Flush(5000)
		ps.kafkaProducer.Close()
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
