package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/enterprise-siem/platform/shared/models"
	"github.com/google/uuid"
)

type CollectorService struct {
	kafkaProducer *kafka.Producer
	syslogServer  *SyslogServer
	config        *Config
}

type Config struct {
	KafkaBrokers   string
	KafkaTopic     string
	SyslogPort     int
	TenantID       string
}

type SyslogServer struct {
	port int
	conn *net.UDPConn
}

func main() {
	config := &Config{
		KafkaBrokers:   getEnv("KAFKA_BROKERS", "localhost:9092"),
		KafkaTopic:     getEnv("KAFKA_TOPIC", "raw-events"),
		SyslogPort:     getEnvInt("SYSLOG_PORT", 514),
		TenantID:       getEnv("TENANT_ID", "default"),
	}

	service, err := NewCollectorService(config)
	if err != nil {
		log.Fatalf("Failed to create collector service: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start syslog server
	go func() {
		if err := service.StartSyslogServer(ctx); err != nil {
			log.Printf("Syslog server error: %v", err)
		}
	}()

	log.Printf("Collector service started. Listening on syslog port %d", config.SyslogPort)

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down collector service...")
	cancel()
	service.Close()
}

func NewCollectorService(config *Config) (*CollectorService, error) {
	// Create Kafka producer
	producer, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": config.KafkaBrokers,
		"client.id":         "siem-collector",
		"acks":              "all",
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create Kafka producer: %w", err)
	}

	syslogServer := &SyslogServer{
		port: config.SyslogPort,
	}

	return &CollectorService{
		kafkaProducer: producer,
		syslogServer:  syslogServer,
		config:        config,
	}, nil
}

func (cs *CollectorService) StartSyslogServer(ctx context.Context) error {
	addr := net.UDPAddr{
		Port: cs.syslogServer.port,
		IP:   net.ParseIP("0.0.0.0"),
	}

	conn, err := net.ListenUDP("udp", &addr)
	if err != nil {
		return fmt.Errorf("failed to start syslog server: %w", err)
	}
	defer conn.Close()

	cs.syslogServer.conn = conn
	log.Printf("Syslog server listening on UDP port %d", cs.syslogServer.port)

	buffer := make([]byte, 8192)

	for {
		select {
		case <-ctx.Done():
			return nil
		default:
			conn.SetReadDeadline(time.Now().Add(1 * time.Second))
			n, remoteAddr, err := conn.ReadFromUDP(buffer)
			if err != nil {
				if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
					continue
				}
				log.Printf("Error reading from UDP: %v", err)
				continue
			}

			// Process the syslog message
			message := string(buffer[:n])
			cs.processSyslogMessage(message, remoteAddr.IP.String())
		}
	}
}

func (cs *CollectorService) processSyslogMessage(message string, sourceIP string) {
	// Create a normalized event
	event := &models.CommonEvent{
		EventID:       uuid.New().String(),
		EventVersion:  "1.0",
		Timestamp:     time.Now(),
		IngestionTime: time.Now(),
		TenantID:      cs.config.TenantID,
		Source: models.Source{
			Type:     "server",
			Category: "system",
			IP:       sourceIP,
		},
		Event: models.Event{
			Type:     "log",
			Action:   "collected",
			Outcome:  "success",
			Severity: "info",
			Category: "operational",
		},
		Metadata: models.Metadata{
			PipelineVersion: "1.0",
			RetentionDays:   30,
		},
		Raw: models.Raw{
			Message: message,
			Format:  "syslog",
		},
	}

	// Send to Kafka
	if err := cs.sendToKafka(event); err != nil {
		log.Printf("Failed to send event to Kafka: %v", err)
	}
}

func (cs *CollectorService) sendToKafka(event *models.CommonEvent) error {
	eventJSON, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	topic := cs.config.KafkaTopic
	err = cs.kafkaProducer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
		Value:          eventJSON,
		Key:            []byte(event.EventID),
	}, nil)

	if err != nil {
		return fmt.Errorf("failed to produce message: %w", err)
	}

	return nil
}

func (cs *CollectorService) Close() {
	if cs.kafkaProducer != nil {
		cs.kafkaProducer.Flush(5000)
		cs.kafkaProducer.Close()
	}
	if cs.syslogServer.conn != nil {
		cs.syslogServer.conn.Close()
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var intValue int
		fmt.Sscanf(value, "%d", &intValue)
		return intValue
	}
	return defaultValue
}
