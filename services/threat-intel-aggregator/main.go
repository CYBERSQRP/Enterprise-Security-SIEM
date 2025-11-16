package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// ThreatIntelAggregator is the main service for collecting and normalizing threat intelligence feeds
type ThreatIntelAggregator struct {
	config         *Config
	feedManager    *FeedManager
	iocProcessor   *IOCProcessor
	httpServer     *http.Server
	metricsServer  *http.Server
	shutdownOnce   sync.Once
}

// Config holds the service configuration
type Config struct {
	Port              string
	MetricsPort       string
	KafkaBrokers      []string
	RedisAddr         string
	PostgresURL       string
	FeedRefreshInterval time.Duration
	MaxConcurrentFeeds  int
	IOCProcessingRate   int
}

// FeedManager manages threat intelligence feeds
type FeedManager struct {
	feeds           map[string]*ThreatFeed
	mu              sync.RWMutex
	refreshInterval time.Duration
	maxConcurrent   int
	metricsCollector *MetricsCollector
}

// ThreatFeed represents a single threat intelligence feed
type ThreatFeed struct {
	ID              string    `json:"id"`
	Name            string    `json:"name"`
	URL             string    `json:"url"`
	Type            string    `json:"type"` // STIX, TAXII, CSV, JSON
	Enabled         bool      `json:"enabled"`
	RefreshInterval int       `json:"refresh_interval"` // minutes
	LastSync        time.Time `json:"last_sync"`
	LastError       string    `json:"last_error,omitempty"`
	IOCCount        int64     `json:"ioc_count"`
	Quality         float64   `json:"quality"` // 0.0 to 1.0
	Confidence      float64   `json:"confidence"` // 0.0 to 1.0
}

// IOC represents an Indicator of Compromise
type IOC struct {
	ID           string            `json:"id"`
	Type         string            `json:"type"` // ip, domain, url, hash, email
	Value        string            `json:"value"`
	FeedID       string            `json:"feed_id"`
	FeedName     string            `json:"feed_name"`
	Confidence   float64           `json:"confidence"`
	Severity     string            `json:"severity"` // critical, high, medium, low
	FirstSeen    time.Time         `json:"first_seen"`
	LastSeen     time.Time         `json:"last_seen"`
	ExpiresAt    *time.Time        `json:"expires_at,omitempty"`
	Tags         []string          `json:"tags"`
	ThreatTypes  []string          `json:"threat_types"`
	Description  string            `json:"description,omitempty"`
	References   []string          `json:"references,omitempty"`
	Metadata     map[string]string `json:"metadata,omitempty"`
}

// IOCProcessor processes and normalizes IOCs from feeds
type IOCProcessor struct {
	processingRate   int
	deduplicator     *IOCDeduplicator
	metricsCollector *MetricsCollector
}

// IOCDeduplicator handles IOC deduplication
type IOCDeduplicator struct {
	cache map[string]*IOC
	mu    sync.RWMutex
}

// MetricsCollector collects Prometheus metrics
type MetricsCollector struct {
	FeedsProcessed    prometheus.Counter
	IOCsProcessed     prometheus.Counter
	FeedErrors        prometheus.Counter
	FeedDuration      prometheus.Histogram
	IOCProcessingRate prometheus.Gauge
	FeedQuality       *prometheus.GaugeVec
}

func NewMetricsCollector() *MetricsCollector {
	mc := &MetricsCollector{
		FeedsProcessed: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "threat_intel_feeds_processed_total",
			Help: "Total number of threat intelligence feeds processed",
		}),
		IOCsProcessed: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "threat_intel_iocs_processed_total",
			Help: "Total number of IOCs processed",
		}),
		FeedErrors: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "threat_intel_feed_errors_total",
			Help: "Total number of feed processing errors",
		}),
		FeedDuration: prometheus.NewHistogram(prometheus.HistogramOpts{
			Name:    "threat_intel_feed_processing_duration_seconds",
			Help:    "Duration of feed processing in seconds",
			Buckets: prometheus.DefBuckets,
		}),
		IOCProcessingRate: prometheus.NewGauge(prometheus.GaugeOpts{
			Name: "threat_intel_ioc_processing_rate",
			Help: "Current IOC processing rate (IOCs/minute)",
		}),
		FeedQuality: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "threat_intel_feed_quality",
				Help: "Quality score of threat intelligence feeds",
			},
			[]string{"feed_id", "feed_name"},
		),
	}

	prometheus.MustRegister(mc.FeedsProcessed)
	prometheus.MustRegister(mc.IOCsProcessed)
	prometheus.MustRegister(mc.FeedErrors)
	prometheus.MustRegister(mc.FeedDuration)
	prometheus.MustRegister(mc.IOCProcessingRate)
	prometheus.MustRegister(mc.FeedQuality)

	return mc
}

func NewThreatIntelAggregator(config *Config) *ThreatIntelAggregator {
	metricsCollector := NewMetricsCollector()

	return &ThreatIntelAggregator{
		config: config,
		feedManager: &FeedManager{
			feeds:           make(map[string]*ThreatFeed),
			refreshInterval: config.FeedRefreshInterval,
			maxConcurrent:   config.MaxConcurrentFeeds,
			metricsCollector: metricsCollector,
		},
		iocProcessor: &IOCProcessor{
			processingRate: config.IOCProcessingRate,
			deduplicator: &IOCDeduplicator{
				cache: make(map[string]*IOC),
			},
			metricsCollector: metricsCollector,
		},
	}
}

func (t *ThreatIntelAggregator) Start(ctx context.Context) error {
	log.Println("Starting Threat Intelligence Aggregator...")

	// Initialize default feeds
	t.initializeDefaultFeeds()

	// Start feed refresh worker
	go t.feedRefreshWorker(ctx)

	// Start IOC processing worker
	go t.iocProcessingWorker(ctx)

	// Start HTTP API server
	if err := t.startHTTPServer(); err != nil {
		return fmt.Errorf("failed to start HTTP server: %w", err)
	}

	// Start metrics server
	if err := t.startMetricsServer(); err != nil {
		return fmt.Errorf("failed to start metrics server: %w", err)
	}

	log.Println("Threat Intelligence Aggregator started successfully")
	return nil
}

func (t *ThreatIntelAggregator) initializeDefaultFeeds() {
	defaultFeeds := []*ThreatFeed{
		{
			ID:              "alienvault-otx",
			Name:            "AlienVault OTX",
			URL:             "https://otx.alienvault.com/api/v1/pulses/subscribed",
			Type:            "JSON",
			Enabled:         true,
			RefreshInterval: 60, // 1 hour
			Quality:         0.85,
			Confidence:      0.80,
		},
		{
			ID:              "abuse-ch-urlhaus",
			Name:            "Abuse.ch URLhaus",
			URL:             "https://urlhaus.abuse.ch/downloads/csv_recent/",
			Type:            "CSV",
			Enabled:         true,
			RefreshInterval: 30, // 30 minutes
			Quality:         0.90,
			Confidence:      0.85,
		},
		{
			ID:              "abuse-ch-feodotracker",
			Name:            "Abuse.ch Feodo Tracker",
			URL:             "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
			Type:            "CSV",
			Enabled:         true,
			RefreshInterval: 60,
			Quality:         0.92,
			Confidence:      0.90,
		},
		{
			ID:              "malware-bazaar",
			Name:            "MalwareBazaar",
			URL:             "https://bazaar.abuse.ch/export/csv/recent/",
			Type:            "CSV",
			Enabled:         true,
			RefreshInterval: 60,
			Quality:         0.88,
			Confidence:      0.85,
		},
		{
			ID:              "phishtank",
			Name:            "PhishTank",
			URL:             "http://data.phishtank.com/data/online-valid.csv",
			Type:            "CSV",
			Enabled:         true,
			RefreshInterval: 120, // 2 hours
			Quality:         0.75,
			Confidence:      0.70,
		},
		{
			ID:              "emergingthreats",
			Name:            "Emerging Threats",
			URL:             "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
			Type:            "TXT",
			Enabled:         true,
			RefreshInterval: 60,
			Quality:         0.88,
			Confidence:      0.85,
		},
	}

	t.feedManager.mu.Lock()
	defer t.feedManager.mu.Unlock()

	for _, feed := range defaultFeeds {
		t.feedManager.feeds[feed.ID] = feed
		log.Printf("Initialized feed: %s (%s)", feed.Name, feed.ID)
	}
}

func (t *ThreatIntelAggregator) feedRefreshWorker(ctx context.Context) {
	ticker := time.NewTicker(5 * time.Minute) // Check every 5 minutes
	defer ticker.Stop()

	// Initial refresh
	t.refreshAllFeeds(ctx)

	for {
		select {
		case <-ctx.Done():
			log.Println("Feed refresh worker stopping...")
			return
		case <-ticker.C:
			t.refreshAllFeeds(ctx)
		}
	}
}

func (t *ThreatIntelAggregator) refreshAllFeeds(ctx context.Context) {
	t.feedManager.mu.RLock()
	feeds := make([]*ThreatFeed, 0, len(t.feedManager.feeds))
	for _, feed := range t.feedManager.feeds {
		if feed.Enabled {
			feeds = append(feeds, feed)
		}
	}
	t.feedManager.mu.RUnlock()

	log.Printf("Refreshing %d active feeds...", len(feeds))

	// Process feeds with concurrency limit
	semaphore := make(chan struct{}, t.feedManager.maxConcurrent)
	var wg sync.WaitGroup

	for _, feed := range feeds {
		// Check if feed needs refresh
		if time.Since(feed.LastSync) < time.Duration(feed.RefreshInterval)*time.Minute {
			continue
		}

		wg.Add(1)
		go func(f *ThreatFeed) {
			defer wg.Done()

			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			t.refreshFeed(ctx, f)
		}(feed)
	}

	wg.Wait()
	log.Println("Feed refresh cycle completed")
}

func (t *ThreatIntelAggregator) refreshFeed(ctx context.Context, feed *ThreatFeed) {
	start := time.Now()
	defer func() {
		duration := time.Since(start)
		t.feedManager.metricsCollector.FeedDuration.Observe(duration.Seconds())
	}()

	log.Printf("Refreshing feed: %s (%s)", feed.Name, feed.ID)

	// Simulate feed processing (in production, this would fetch and parse the feed)
	// For now, we'll just update the sync time and metrics

	t.feedManager.metricsCollector.FeedsProcessed.Inc()

	// Update feed metadata
	t.feedManager.mu.Lock()
	feed.LastSync = time.Now()
	feed.LastError = ""
	// Simulate IOC count (in production, this would be actual count)
	feed.IOCCount += int64(100 + (time.Now().Unix() % 500))
	t.feedManager.mu.Unlock()

	// Update quality metric
	t.feedManager.metricsCollector.FeedQuality.WithLabelValues(feed.ID, feed.Name).Set(feed.Quality)

	log.Printf("Feed refreshed successfully: %s (IOCs: %d)", feed.Name, feed.IOCCount)
}

func (t *ThreatIntelAggregator) iocProcessingWorker(ctx context.Context) {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			log.Println("IOC processing worker stopping...")
			return
		case <-ticker.C:
			// Simulate IOC processing rate
			rate := float64(t.iocProcessor.processingRate)
			t.iocProcessor.metricsCollector.IOCProcessingRate.Set(rate)
		}
	}
}

func (t *ThreatIntelAggregator) startHTTPServer() error {
	router := mux.NewRouter()

	// API routes
	router.HandleFunc("/health", t.healthHandler).Methods("GET")
	router.HandleFunc("/ready", t.readyHandler).Methods("GET")
	router.HandleFunc("/api/v1/feeds", t.listFeedsHandler).Methods("GET")
	router.HandleFunc("/api/v1/feeds/{id}", t.getFeedHandler).Methods("GET")
	router.HandleFunc("/api/v1/feeds/{id}", t.updateFeedHandler).Methods("PUT")
	router.HandleFunc("/api/v1/feeds/{id}/refresh", t.refreshFeedHandler).Methods("POST")
	router.HandleFunc("/api/v1/iocs/search", t.searchIOCsHandler).Methods("POST")
	router.HandleFunc("/api/v1/iocs/{value}", t.lookupIOCHandler).Methods("GET")

	t.httpServer = &http.Server{
		Addr:         ":" + t.config.Port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("HTTP API server listening on :%s", t.config.Port)
		if err := t.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	return nil
}

func (t *ThreatIntelAggregator) startMetricsServer() error {
	metricsRouter := mux.NewRouter()
	metricsRouter.Handle("/metrics", promhttp.Handler())

	t.metricsServer = &http.Server{
		Addr:    ":" + t.config.MetricsPort,
		Handler: metricsRouter,
	}

	go func() {
		log.Printf("Metrics server listening on :%s", t.config.MetricsPort)
		if err := t.metricsServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Metrics server error: %v", err)
		}
	}()

	return nil
}

// HTTP Handlers

func (t *ThreatIntelAggregator) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func (t *ThreatIntelAggregator) readyHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

func (t *ThreatIntelAggregator) listFeedsHandler(w http.ResponseWriter, r *http.Request) {
	t.feedManager.mu.RLock()
	defer t.feedManager.mu.RUnlock()

	feeds := make([]*ThreatFeed, 0, len(t.feedManager.feeds))
	for _, feed := range t.feedManager.feeds {
		feeds = append(feeds, feed)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"feeds": feeds,
		"count": len(feeds),
	})
}

func (t *ThreatIntelAggregator) getFeedHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	feedID := vars["id"]

	t.feedManager.mu.RLock()
	feed, exists := t.feedManager.feeds[feedID]
	t.feedManager.mu.RUnlock()

	if !exists {
		http.Error(w, "Feed not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(feed)
}

func (t *ThreatIntelAggregator) updateFeedHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	feedID := vars["id"]

	var updates map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	t.feedManager.mu.Lock()
	feed, exists := t.feedManager.feeds[feedID]
	if !exists {
		t.feedManager.mu.Unlock()
		http.Error(w, "Feed not found", http.StatusNotFound)
		return
	}

	// Update enabled status if provided
	if enabled, ok := updates["enabled"].(bool); ok {
		feed.Enabled = enabled
	}

	t.feedManager.mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(feed)
}

func (t *ThreatIntelAggregator) refreshFeedHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	feedID := vars["id"]

	t.feedManager.mu.RLock()
	feed, exists := t.feedManager.feeds[feedID]
	t.feedManager.mu.RUnlock()

	if !exists {
		http.Error(w, "Feed not found", http.StatusNotFound)
		return
	}

	// Trigger immediate refresh
	go t.refreshFeed(r.Context(), feed)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "refresh_started",
		"feed_id": feedID,
	})
}

func (t *ThreatIntelAggregator) searchIOCsHandler(w http.ResponseWriter, r *http.Request) {
	var searchReq struct {
		Type     string   `json:"type,omitempty"`
		Tags     []string `json:"tags,omitempty"`
		Severity string   `json:"severity,omitempty"`
		Limit    int      `json:"limit,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&searchReq); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if searchReq.Limit == 0 {
		searchReq.Limit = 100
	}

	// In production, this would query the database
	// For now, return empty results
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"iocs":  []IOC{},
		"count": 0,
		"total": 0,
	})
}

func (t *ThreatIntelAggregator) lookupIOCHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	value := vars["value"]

	// In production, this would lookup the IOC in the database
	// For now, return not found
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"found": false,
		"value": value,
	})
}

func (t *ThreatIntelAggregator) Shutdown(ctx context.Context) error {
	var shutdownErr error

	t.shutdownOnce.Do(func() {
		log.Println("Shutting down Threat Intelligence Aggregator...")

		// Shutdown HTTP server
		if t.httpServer != nil {
			if err := t.httpServer.Shutdown(ctx); err != nil {
				log.Printf("Error shutting down HTTP server: %v", err)
				shutdownErr = err
			}
		}

		// Shutdown metrics server
		if t.metricsServer != nil {
			if err := t.metricsServer.Shutdown(ctx); err != nil {
				log.Printf("Error shutting down metrics server: %v", err)
				shutdownErr = err
			}
		}

		log.Println("Threat Intelligence Aggregator shutdown complete")
	})

	return shutdownErr
}

func main() {
	config := &Config{
		Port:                getEnv("PORT", "8080"),
		MetricsPort:         getEnv("METRICS_PORT", "9090"),
		KafkaBrokers:        []string{getEnv("KAFKA_BROKERS", "localhost:9092")},
		RedisAddr:           getEnv("REDIS_ADDR", "localhost:6379"),
		PostgresURL:         getEnv("POSTGRES_URL", "postgresql://localhost:5432/siem"),
		FeedRefreshInterval: 5 * time.Minute,
		MaxConcurrentFeeds:  10,
		IOCProcessingRate:   100000, // 100K IOCs/minute
	}

	aggregator := NewThreatIntelAggregator(config)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := aggregator.Start(ctx); err != nil {
		log.Fatalf("Failed to start aggregator: %v", err)
	}

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	log.Println("Received shutdown signal")

	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := aggregator.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Error during shutdown: %v", err)
	}

	log.Println("Service stopped")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
