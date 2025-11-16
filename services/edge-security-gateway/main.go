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

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// EdgeGateway manages edge computing and IoT security
type EdgeGateway struct {
	router          *gin.Engine
	devices         map[string]*EdgeDevice
	devicesMutex    sync.RWMutex
	anomalyDetector *AnomalyDetector
	edgeRules       map[string]*EdgeRule
	collectors      map[string]*DataCollector
}

// EdgeDevice represents an IoT or edge device
type EdgeDevice struct {
	DeviceID       string                 `json:"device_id"`
	DeviceType     string                 `json:"device_type"`
	Location       string                 `json:"location"`
	Status         string                 `json:"status"`
	LastSeen       time.Time              `json:"last_seen"`
	IPAddress      string                 `json:"ip_address"`
	MACAddress     string                 `json:"mac_address"`
	Firmware       string                 `json:"firmware"`
	SecurityScore  float64                `json:"security_score"`
	Capabilities   []string               `json:"capabilities"`
	Telemetry      map[string]interface{} `json:"telemetry"`
	ThreatLevel    string                 `json:"threat_level"`
	IsCompromised  bool                   `json:"is_compromised"`
	LastAlert      *SecurityAlert         `json:"last_alert,omitempty"`
}

// SecurityAlert represents a security event from edge devices
type SecurityAlert struct {
	AlertID      string    `json:"alert_id"`
	DeviceID     string    `json:"device_id"`
	Severity     string    `json:"severity"`
	AlertType    string    `json:"alert_type"`
	Description  string    `json:"description"`
	Timestamp    time.Time `json:"timestamp"`
	Indicators   []string  `json:"indicators"`
	Mitigation   string    `json:"mitigation"`
}

// EdgeRule represents security rules executed at the edge
type EdgeRule struct {
	RuleID      string   `json:"rule_id"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Condition   string   `json:"condition"`
	Action      string   `json:"action"`
	Severity    string   `json:"severity"`
	DeviceTypes []string `json:"device_types"`
	Enabled     bool     `json:"enabled"`
}

// AnomalyDetector detects abnormal behavior in edge devices
type AnomalyDetector struct {
	baselines       map[string]*DeviceBaseline
	anomalies       []Anomaly
	detectionModels map[string]*DetectionModel
}

// DeviceBaseline represents normal behavior patterns
type DeviceBaseline struct {
	DeviceID           string    `json:"device_id"`
	AvgCPUUsage        float64   `json:"avg_cpu_usage"`
	AvgMemoryUsage     float64   `json:"avg_memory_usage"`
	AvgNetworkTraffic  float64   `json:"avg_network_traffic"`
	TypicalConnections []string  `json:"typical_connections"`
	TypicalProcesses   []string  `json:"typical_processes"`
	LastUpdated        time.Time `json:"last_updated"`
}

// Anomaly represents detected abnormal behavior
type Anomaly struct {
	AnomalyID   string    `json:"anomaly_id"`
	DeviceID    string    `json:"device_id"`
	Type        string    `json:"type"`
	Severity    string    `json:"severity"`
	Score       float64   `json:"score"`
	Description string    `json:"description"`
	Timestamp   time.Time `json:"timestamp"`
}

// DetectionModel represents edge ML model
type DetectionModel struct {
	ModelID     string    `json:"model_id"`
	Name        string    `json:"name"`
	Type        string    `json:"type"`
	Version     string    `json:"version"`
	Accuracy    float64   `json:"accuracy"`
	LastTrained time.Time `json:"last_trained"`
	Deployed    bool      `json:"deployed"`
}

// DataCollector handles data collection from edge devices
type DataCollector struct {
	CollectorID     string   `json:"collector_id"`
	Protocol        string   `json:"protocol"`
	Port            int      `json:"port"`
	SupportedTypes  []string `json:"supported_types"`
	EventsCollected int64    `json:"events_collected"`
	IsActive        bool     `json:"is_active"`
}

// Telemetry requests
type TelemetryUpdate struct {
	DeviceID  string                 `json:"device_id"`
	Timestamp time.Time              `json:"timestamp"`
	Metrics   map[string]interface{} `json:"metrics"`
}

type DeviceRegistration struct {
	DeviceID     string   `json:"device_id"`
	DeviceType   string   `json:"device_type"`
	Location     string   `json:"location"`
	IPAddress    string   `json:"ip_address"`
	MACAddress   string   `json:"mac_address"`
	Firmware     string   `json:"firmware"`
	Capabilities []string `json:"capabilities"`
}

var (
	// Prometheus metrics
	edgeDevicesTotal = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "edge_devices_total",
			Help: "Total number of registered edge devices",
		},
		[]string{"device_type", "status"},
	)

	edgeAlertsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "edge_alerts_total",
			Help: "Total number of edge security alerts",
		},
		[]string{"severity", "alert_type"},
	)

	edgeAnomaliesDetected = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "edge_anomalies_detected_total",
			Help: "Total number of anomalies detected",
		},
		[]string{"device_type", "anomaly_type"},
	)

	edgeTelemetryEvents = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "edge_telemetry_events_total",
			Help: "Total number of telemetry events received",
		},
	)

	edgeProcessingLatency = prometheus.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "edge_processing_latency_seconds",
			Help:    "Edge data processing latency",
			Buckets: prometheus.DefBuckets,
		},
	)
)

func init() {
	prometheus.MustRegister(edgeDevicesTotal)
	prometheus.MustRegister(edgeAlertsTotal)
	prometheus.MustRegister(edgeAnomaliesDetected)
	prometheus.MustRegister(edgeTelemetryEvents)
	prometheus.MustRegister(edgeProcessingLatency)
}

// NewEdgeGateway creates a new Edge Security Gateway
func NewEdgeGateway() *EdgeGateway {
	router := gin.Default()

	gateway := &EdgeGateway{
		router:   router,
		devices:  make(map[string]*EdgeDevice),
		edgeRules: make(map[string]*EdgeRule),
		collectors: make(map[string]*DataCollector),
		anomalyDetector: &AnomalyDetector{
			baselines:       make(map[string]*DeviceBaseline),
			anomalies:       make([]Anomaly, 0),
			detectionModels: make(map[string]*DetectionModel),
		},
	}

	// Initialize default edge rules
	gateway.initializeDefaultRules()

	// Initialize data collectors
	gateway.initializeCollectors()

	// Initialize detection models
	gateway.initializeDetectionModels()

	gateway.setupRoutes()
	return gateway
}

func (g *EdgeGateway) initializeDefaultRules() {
	g.edgeRules["rule-001"] = &EdgeRule{
		RuleID:      "rule-001",
		Name:        "Suspicious Network Activity",
		Description: "Detect unusual network connections from IoT devices",
		Condition:   "connections > baseline + 3*stddev",
		Action:      "alert",
		Severity:    "high",
		DeviceTypes: []string{"iot", "sensor", "camera"},
		Enabled:     true,
	}

	g.edgeRules["rule-002"] = &EdgeRule{
		RuleID:      "rule-002",
		Name:        "Firmware Version Mismatch",
		Description: "Detect outdated or unauthorized firmware",
		Condition:   "firmware != approved_version",
		Action:      "isolate",
		Severity:    "critical",
		DeviceTypes: []string{"all"},
		Enabled:     true,
	}

	g.edgeRules["rule-003"] = &EdgeRule{
		RuleID:      "rule-003",
		Name:        "High Resource Usage",
		Description: "Detect abnormal CPU or memory usage",
		Condition:   "cpu > 80% OR memory > 90%",
		Action:      "investigate",
		Severity:    "medium",
		DeviceTypes: []string{"edge-server", "gateway"},
		Enabled:     true,
	}
}

func (g *EdgeGateway) initializeCollectors() {
	g.collectors["mqtt-collector"] = &DataCollector{
		CollectorID:     "mqtt-collector",
		Protocol:        "MQTT",
		Port:            1883,
		SupportedTypes:  []string{"sensor", "actuator"},
		EventsCollected: 0,
		IsActive:        true,
	}

	g.collectors["coap-collector"] = &DataCollector{
		CollectorID:     "coap-collector",
		Protocol:        "CoAP",
		Port:            5683,
		SupportedTypes:  []string{"constrained-device"},
		EventsCollected: 0,
		IsActive:        true,
	}

	g.collectors["http-collector"] = &DataCollector{
		CollectorID:     "http-collector",
		Protocol:        "HTTP",
		Port:            8087,
		SupportedTypes:  []string{"camera", "edge-server"},
		EventsCollected: 0,
		IsActive:        true,
	}
}

func (g *EdgeGateway) initializeDetectionModels() {
	g.anomalyDetector.detectionModels["network-anomaly"] = &DetectionModel{
		ModelID:     "network-anomaly",
		Name:        "Network Anomaly Detection",
		Type:        "LSTM",
		Version:     "1.0.0",
		Accuracy:    0.92,
		LastTrained: time.Now().Add(-24 * time.Hour),
		Deployed:    true,
	}

	g.anomalyDetector.detectionModels["behavior-anomaly"] = &DetectionModel{
		ModelID:     "behavior-anomaly",
		Name:        "Device Behavior Analysis",
		Type:        "Isolation Forest",
		Version:     "1.1.0",
		Accuracy:    0.89,
		LastTrained: time.Now().Add(-48 * time.Hour),
		Deployed:    true,
	}
}

func (g *EdgeGateway) setupRoutes() {
	// Health check
	g.router.GET("/health", g.healthHandler)

	// API routes
	api := g.router.Group("/api/v1")
	{
		// Device management
		api.POST("/devices/register", g.registerDeviceHandler)
		api.GET("/devices", g.listDevicesHandler)
		api.GET("/devices/:id", g.getDeviceHandler)
		api.DELETE("/devices/:id", g.deregisterDeviceHandler)

		// Telemetry
		api.POST("/telemetry", g.receiveTelemetryHandler)
		api.GET("/telemetry/:device_id", g.getDeviceTelemetryHandler)

		// Alerts
		api.GET("/alerts", g.listAlertsHandler)
		api.GET("/alerts/:device_id", g.getDeviceAlertsHandler)

		// Edge rules
		api.GET("/rules", g.listRulesHandler)
		api.POST("/rules", g.createRuleHandler)
		api.PUT("/rules/:id", g.updateRuleHandler)
		api.DELETE("/rules/:id", g.deleteRuleHandler)

		// Anomaly detection
		api.GET("/anomalies", g.listAnomaliesHandler)
		api.GET("/baselines/:device_id", g.getBaselineHandler)

		// Detection models
		api.GET("/models", g.listModelsHandler)
		api.POST("/models/:id/deploy", g.deployModelHandler)

		// Collectors
		api.GET("/collectors", g.listCollectorsHandler)
	}

	// Metrics
	g.router.GET("/metrics", gin.WrapH(promhttp.Handler()))
}

func (g *EdgeGateway) healthHandler(c *gin.Context) {
	g.devicesMutex.RLock()
	activeDevices := 0
	for _, device := range g.devices {
		if device.Status == "active" {
			activeDevices++
		}
	}
	g.devicesMutex.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"status":         "healthy",
		"service":        "edge-security-gateway",
		"timestamp":      time.Now().Unix(),
		"devices":        len(g.devices),
		"active_devices": activeDevices,
		"rules":          len(g.edgeRules),
		"collectors":     len(g.collectors),
	})
}

func (g *EdgeGateway) registerDeviceHandler(c *gin.Context) {
	var req DeviceRegistration
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	device := &EdgeDevice{
		DeviceID:      req.DeviceID,
		DeviceType:    req.DeviceType,
		Location:      req.Location,
		Status:        "active",
		LastSeen:      time.Now(),
		IPAddress:     req.IPAddress,
		MACAddress:    req.MACAddress,
		Firmware:      req.Firmware,
		SecurityScore: 85.0,
		Capabilities:  req.Capabilities,
		Telemetry:     make(map[string]interface{}),
		ThreatLevel:   "low",
		IsCompromised: false,
	}

	g.devicesMutex.Lock()
	g.devices[req.DeviceID] = device
	g.devicesMutex.Unlock()

	// Create baseline
	g.anomalyDetector.baselines[req.DeviceID] = &DeviceBaseline{
		DeviceID:           req.DeviceID,
		AvgCPUUsage:        15.0,
		AvgMemoryUsage:     30.0,
		AvgNetworkTraffic:  1024.0,
		TypicalConnections: []string{},
		TypicalProcesses:   []string{},
		LastUpdated:        time.Now(),
	}

	edgeDevicesTotal.WithLabelValues(req.DeviceType, "active").Inc()

	log.Printf("Registered edge device: %s (%s)", req.DeviceID, req.DeviceType)

	c.JSON(http.StatusCreated, gin.H{
		"status":  "registered",
		"device":  device,
	})
}

func (g *EdgeGateway) listDevicesHandler(c *gin.Context) {
	g.devicesMutex.RLock()
	defer g.devicesMutex.RUnlock()

	devices := make([]*EdgeDevice, 0, len(g.devices))
	for _, device := range g.devices {
		devices = append(devices, device)
	}

	c.JSON(http.StatusOK, gin.H{
		"devices": devices,
		"count":   len(devices),
	})
}

func (g *EdgeGateway) getDeviceHandler(c *gin.Context) {
	deviceID := c.Param("id")

	g.devicesMutex.RLock()
	device, exists := g.devices[deviceID]
	g.devicesMutex.RUnlock()

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "device not found"})
		return
	}

	c.JSON(http.StatusOK, device)
}

func (g *EdgeGateway) receiveTelemetryHandler(c *gin.Context) {
	var telemetry TelemetryUpdate
	if err := c.ShouldBindJSON(&telemetry); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	start := time.Now()

	g.devicesMutex.Lock()
	device, exists := g.devices[telemetry.DeviceID]
	if exists {
		device.LastSeen = telemetry.Timestamp
		device.Telemetry = telemetry.Metrics

		// Check for anomalies
		anomaly := g.detectAnomalies(device, telemetry.Metrics)
		if anomaly != nil {
			g.anomalyDetector.anomalies = append(g.anomalyDetector.anomalies, *anomaly)
			edgeAnomaliesDetected.WithLabelValues(device.DeviceType, anomaly.Type).Inc()

			// Create alert if severe
			if anomaly.Severity == "high" || anomaly.Severity == "critical" {
				alert := &SecurityAlert{
					AlertID:     fmt.Sprintf("alert-%d", time.Now().Unix()),
					DeviceID:    device.DeviceID,
					Severity:    anomaly.Severity,
					AlertType:   anomaly.Type,
					Description: anomaly.Description,
					Timestamp:   time.Now(),
					Indicators:  []string{anomaly.Type},
					Mitigation:  "Investigate device behavior",
				}
				device.LastAlert = alert
				edgeAlertsTotal.WithLabelValues(alert.Severity, alert.AlertType).Inc()
			}
		}
	}
	g.devicesMutex.Unlock()

	edgeTelemetryEvents.Inc()
	edgeProcessingLatency.Observe(time.Since(start).Seconds())

	c.JSON(http.StatusOK, gin.H{
		"status":    "received",
		"device_id": telemetry.DeviceID,
		"timestamp": telemetry.Timestamp,
	})
}

func (g *EdgeGateway) detectAnomalies(device *EdgeDevice, metrics map[string]interface{}) *Anomaly {
	baseline, exists := g.anomalyDetector.baselines[device.DeviceID]
	if !exists {
		return nil
	}

	// Check CPU anomaly
	if cpu, ok := metrics["cpu_usage"].(float64); ok {
		if cpu > baseline.AvgCPUUsage*2.0 {
			return &Anomaly{
				AnomalyID:   fmt.Sprintf("anomaly-%d", time.Now().Unix()),
				DeviceID:    device.DeviceID,
				Type:        "cpu_spike",
				Severity:    "medium",
				Score:       0.75,
				Description: fmt.Sprintf("CPU usage %.1f%% exceeds baseline %.1f%%", cpu, baseline.AvgCPUUsage),
				Timestamp:   time.Now(),
			}
		}
	}

	// Check memory anomaly
	if memory, ok := metrics["memory_usage"].(float64); ok {
		if memory > baseline.AvgMemoryUsage*2.0 {
			return &Anomaly{
				AnomalyID:   fmt.Sprintf("anomaly-%d", time.Now().Unix()),
				DeviceID:    device.DeviceID,
				Type:        "memory_spike",
				Severity:    "medium",
				Score:       0.70,
				Description: fmt.Sprintf("Memory usage %.1f%% exceeds baseline %.1f%%", memory, baseline.AvgMemoryUsage),
				Timestamp:   time.Now(),
			}
		}
	}

	return nil
}

func (g *EdgeGateway) deregisterDeviceHandler(c *gin.Context) {
	deviceID := c.Param("id")

	g.devicesMutex.Lock()
	device, exists := g.devices[deviceID]
	if exists {
		edgeDevicesTotal.WithLabelValues(device.DeviceType, device.Status).Dec()
		delete(g.devices, deviceID)
	}
	g.devicesMutex.Unlock()

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "device not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "deregistered", "device_id": deviceID})
}

func (g *EdgeGateway) getDeviceTelemetryHandler(c *gin.Context) {
	deviceID := c.Param("device_id")

	g.devicesMutex.RLock()
	device, exists := g.devices[deviceID]
	g.devicesMutex.RUnlock()

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "device not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"device_id":  deviceID,
		"telemetry":  device.Telemetry,
		"last_seen":  device.LastSeen,
	})
}

func (g *EdgeGateway) listAlertsHandler(c *gin.Context) {
	alerts := make([]*SecurityAlert, 0)

	g.devicesMutex.RLock()
	for _, device := range g.devices {
		if device.LastAlert != nil {
			alerts = append(alerts, device.LastAlert)
		}
	}
	g.devicesMutex.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"alerts": alerts,
		"count":  len(alerts),
	})
}

func (g *EdgeGateway) getDeviceAlertsHandler(c *gin.Context) {
	deviceID := c.Param("device_id")

	g.devicesMutex.RLock()
	device, exists := g.devices[deviceID]
	g.devicesMutex.RUnlock()

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "device not found"})
		return
	}

	alerts := []*SecurityAlert{}
	if device.LastAlert != nil {
		alerts = append(alerts, device.LastAlert)
	}

	c.JSON(http.StatusOK, gin.H{
		"device_id": deviceID,
		"alerts":    alerts,
		"count":     len(alerts),
	})
}

func (g *EdgeGateway) listRulesHandler(c *gin.Context) {
	rules := make([]*EdgeRule, 0)
	for _, rule := range g.edgeRules {
		rules = append(rules, rule)
	}

	c.JSON(http.StatusOK, gin.H{
		"rules": rules,
		"count": len(rules),
	})
}

func (g *EdgeGateway) createRuleHandler(c *gin.Context) {
	var rule EdgeRule
	if err := c.ShouldBindJSON(&rule); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	rule.RuleID = fmt.Sprintf("rule-%d", time.Now().Unix())
	g.edgeRules[rule.RuleID] = &rule

	c.JSON(http.StatusCreated, rule)
}

func (g *EdgeGateway) updateRuleHandler(c *gin.Context) {
	ruleID := c.Param("id")

	var rule EdgeRule
	if err := c.ShouldBindJSON(&rule); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if _, exists := g.edgeRules[ruleID]; !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "rule not found"})
		return
	}

	rule.RuleID = ruleID
	g.edgeRules[ruleID] = &rule

	c.JSON(http.StatusOK, rule)
}

func (g *EdgeGateway) deleteRuleHandler(c *gin.Context) {
	ruleID := c.Param("id")

	if _, exists := g.edgeRules[ruleID]; !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "rule not found"})
		return
	}

	delete(g.edgeRules, ruleID)

	c.JSON(http.StatusOK, gin.H{"status": "deleted", "rule_id": ruleID})
}

func (g *EdgeGateway) listAnomaliesHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"anomalies": g.anomalyDetector.anomalies,
		"count":     len(g.anomalyDetector.anomalies),
	})
}

func (g *EdgeGateway) getBaselineHandler(c *gin.Context) {
	deviceID := c.Param("device_id")

	baseline, exists := g.anomalyDetector.baselines[deviceID]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "baseline not found"})
		return
	}

	c.JSON(http.StatusOK, baseline)
}

func (g *EdgeGateway) listModelsHandler(c *gin.Context) {
	models := make([]*DetectionModel, 0)
	for _, model := range g.anomalyDetector.detectionModels {
		models = append(models, model)
	}

	c.JSON(http.StatusOK, gin.H{
		"models": models,
		"count":  len(models),
	})
}

func (g *EdgeGateway) deployModelHandler(c *gin.Context) {
	modelID := c.Param("id")

	model, exists := g.anomalyDetector.detectionModels[modelID]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{"error": "model not found"})
		return
	}

	model.Deployed = true
	model.LastTrained = time.Now()

	c.JSON(http.StatusOK, gin.H{
		"status": "deployed",
		"model":  model,
	})
}

func (g *EdgeGateway) listCollectorsHandler(c *gin.Context) {
	collectors := make([]*DataCollector, 0)
	for _, collector := range g.collectors {
		collectors = append(collectors, collector)
	}

	c.JSON(http.StatusOK, gin.H{
		"collectors": collectors,
		"count":      len(collectors),
	})
}

func (g *EdgeGateway) Start() error {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8087"
	}

	srv := &http.Server{
		Addr:    ":" + port,
		Handler: g.router,
	}

	// Graceful shutdown
	go func() {
		sigint := make(chan os.Signal, 1)
		signal.Notify(sigint, os.Interrupt, syscall.SIGTERM)
		<-sigint

		log.Println("Shutting down server...")
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			log.Printf("Server shutdown error: %v", err)
		}
	}()

	log.Printf("Edge Security Gateway starting on port %s", port)
	return srv.ListenAndServe()
}

func main() {
	gateway := NewEdgeGateway()
	if err := gateway.Start(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Failed to start service: %v", err)
	}
}
