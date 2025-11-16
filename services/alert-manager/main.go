package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/enterprise-siem/alert-manager/internal/api"
	"github.com/enterprise-siem/alert-manager/internal/config"
	"github.com/enterprise-siem/alert-manager/internal/consumer"
	"github.com/enterprise-siem/alert-manager/internal/notification"
	"github.com/enterprise-siem/alert-manager/internal/storage"
	"github.com/gin-gonic/gin"
	log "github.com/sirupsen/logrus"
)

func main() {
	log.SetFormatter(&log.JSONFormatter{})
	log.SetLevel(log.InfoLevel)

	log.Info("Starting Alert Manager Service")

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize storage
	store, err := storage.New(cfg.Database.URL, cfg.Redis.URL)
	if err != nil {
		log.Fatalf("Failed to initialize storage: %v", err)
	}
	defer store.Close()

	// Initialize notification service
	notifier := notification.New(cfg.Notifications)

	// Initialize Kafka consumer
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	kafkaConsumer := consumer.New(cfg.Kafka, store, notifier)
	go func() {
		if err := kafkaConsumer.Start(ctx); err != nil {
			log.Errorf("Kafka consumer error: %v", err)
		}
	}()

	// Initialize HTTP server
	router := gin.Default()
	api.SetupRoutes(router, store, notifier)

	srv := &api.Server{
		Router: router,
		Store:  store,
	}

	// Start HTTP server
	go func() {
		addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
		log.Infof("Starting HTTP server on %s", addr)
		if err := srv.Start(addr); err != nil {
			log.Errorf("HTTP server error: %v", err)
		}
	}()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Info("Shutting down Alert Manager Service")
	cancel()
	time.Sleep(2 * time.Second)
}
