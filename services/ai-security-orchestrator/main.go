package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Service represents the AI Security Orchestrator service
type Service struct {
	router       *gin.Engine
	aiEngine     *AIEngine
	actionEngine *ActionEngine
	decisionLog  []Decision
}

// AIEngine handles autonomous decision making
type AIEngine struct {
	models         map[string]*MLModel
	confidenceMin  float64
	learningEngine *ReinforcementLearning
}

// MLModel represents a machine learning model
type MLModel struct {
	Name           string    `json:"name"`
	Type           string    `json:"type"`
	Version        string    `json:"version"`
	Accuracy       float64   `json:"accuracy"`
	LastTrained    time.Time `json:"last_trained"`
	Enabled        bool      `json:"enabled"`
}

// ActionEngine executes autonomous response actions
type ActionEngine struct {
	actions         map[string]Action
	executionPolicy ExecutionPolicy
	safetyLimits    SafetyLimits
}

// Action represents an autonomous response action
type Action struct {
	ID            string    `json:"id"`
	Type          string    `json:"type"`
	Description   string    `json:"description"`
	RiskLevel     string    `json:"risk_level"`
	RequiresApproval bool   `json:"requires_approval"`
	ExecutionCount int      `json:"execution_count"`
	SuccessRate   float64   `json:"success_rate"`
}

// ExecutionPolicy defines when autonomous actions are allowed
type ExecutionPolicy struct {
	AutoApproveThreshold  float64   `json:"auto_approve_threshold"`
	MaxActionsPerHour     int       `json:"max_actions_per_hour"`
	CriticalActionsOnly   bool      `json:"critical_actions_only"`
	BusinessHoursOnly     bool      `json:"business_hours_only"`
	ExcludedAssets        []string  `json:"excluded_assets"`
}

// SafetyLimits ensures autonomous actions don't cause harm
type SafetyLimits struct {
	MaxImpactedAssets     int       `json:"max_impacted_assets"`
	MaxNetworkDisruption  float64   `json:"max_network_disruption"`
	RollbackRequired      bool      `json:"rollback_required"`
	HumanApprovalThreshold float64  `json:"human_approval_threshold"`
}

// Decision represents an autonomous decision made by the AI
type Decision struct {
	ID              string    `json:"id"`
	Timestamp       time.Time `json:"timestamp"`
	IncidentID      string    `json:"incident_id"`
	Severity        string    `json:"severity"`
	Confidence      float64   `json:"confidence"`
	RecommendedAction string  `json:"recommended_action"`
	AutoExecuted    bool      `json:"auto_executed"`
	Rationale       string    `json:"rationale"`
	Outcome         string    `json:"outcome"`
}

// ReinforcementLearning learns from action outcomes
type ReinforcementLearning struct {
	StateActionValues map[string]float64
	LearningRate      float64
	DiscountFactor    float64
	ExplorationRate   float64
}

// IncidentRequest represents an incoming incident for autonomous response
type IncidentRequest struct {
	IncidentID      string                 `json:"incident_id"`
	Severity        string                 `json:"severity"`
	ThreatType      string                 `json:"threat_type"`
	AffectedAssets  []string               `json:"affected_assets"`
	Indicators      []string               `json:"indicators"`
	Metadata        map[string]interface{} `json:"metadata"`
	RequireApproval bool                   `json:"require_approval"`
}

// ResponseRecommendation represents the AI's recommended response
type ResponseRecommendation struct {
	Decision        Decision  `json:"decision"`
	Actions         []Action  `json:"actions"`
	ImpactAnalysis  Impact    `json:"impact_analysis"`
	ExecutionPlan   string    `json:"execution_plan"`
	Alternatives    []string  `json:"alternatives"`
}

// Impact represents the predicted impact of an action
type Impact struct {
	AffectedSystems    int     `json:"affected_systems"`
	ServiceDisruption  string  `json:"service_disruption"`
	DataLoss           string  `json:"data_loss"`
	ConfidenceLevel    float64 `json:"confidence_level"`
}

var (
	// Prometheus metrics
	decisionsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ai_orchestrator_decisions_total",
			Help: "Total number of autonomous decisions made",
		},
		[]string{"auto_executed", "severity"},
	)

	actionsExecuted = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ai_orchestrator_actions_executed_total",
			Help: "Total number of autonomous actions executed",
		},
		[]string{"action_type", "success"},
	)

	decisionLatency = prometheus.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "ai_orchestrator_decision_latency_seconds",
			Help:    "Time taken to make autonomous decisions",
			Buckets: prometheus.DefBuckets,
		},
	)

	confidenceScore = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "ai_orchestrator_confidence_score",
			Help: "Confidence score of the last decision",
		},
		[]string{"incident_id"},
	)
)

func init() {
	prometheus.MustRegister(decisionsTotal)
	prometheus.MustRegister(actionsExecuted)
	prometheus.MustRegister(decisionLatency)
	prometheus.MustRegister(confidenceScore)
}

// NewService creates a new AI Security Orchestrator service
func NewService() *Service {
	router := gin.Default()

	aiEngine := &AIEngine{
		models:        make(map[string]*MLModel),
		confidenceMin: 0.85,
		learningEngine: &ReinforcementLearning{
			StateActionValues: make(map[string]float64),
			LearningRate:      0.1,
			DiscountFactor:    0.95,
			ExplorationRate:   0.1,
		},
	}

	// Initialize ML models
	aiEngine.models["incident_classification"] = &MLModel{
		Name:        "Incident Classification",
		Type:        "Random Forest",
		Version:     "1.2.0",
		Accuracy:    0.94,
		LastTrained: time.Now().Add(-24 * time.Hour),
		Enabled:     true,
	}
	aiEngine.models["threat_prediction"] = &MLModel{
		Name:        "Threat Prediction",
		Type:        "LSTM Neural Network",
		Version:     "2.0.1",
		Accuracy:    0.91,
		LastTrained: time.Now().Add(-12 * time.Hour),
		Enabled:     true,
	}
	aiEngine.models["response_optimization"] = &MLModel{
		Name:        "Response Optimization",
		Type:        "Deep Q-Network",
		Version:     "1.5.3",
		Accuracy:    0.89,
		LastTrained: time.Now().Add(-6 * time.Hour),
		Enabled:     true,
	}

	actionEngine := &ActionEngine{
		actions: map[string]Action{
			"isolate_host":        {ID: "isolate_host", Type: "containment", Description: "Isolate compromised host", RiskLevel: "medium", RequiresApproval: false, SuccessRate: 0.98},
			"block_ip":            {ID: "block_ip", Type: "network", Description: "Block malicious IP", RiskLevel: "low", RequiresApproval: false, SuccessRate: 0.99},
			"disable_account":     {ID: "disable_account", Type: "identity", Description: "Disable compromised account", RiskLevel: "medium", RequiresApproval: false, SuccessRate: 0.97},
			"quarantine_email":    {ID: "quarantine_email", Type: "email", Description: "Quarantine phishing email", RiskLevel: "low", RequiresApproval: false, SuccessRate: 0.99},
			"kill_process":        {ID: "kill_process", Type: "endpoint", Description: "Terminate malicious process", RiskLevel: "high", RequiresApproval: true, SuccessRate: 0.95},
			"shutdown_service":    {ID: "shutdown_service", Type: "infrastructure", Description: "Shutdown compromised service", RiskLevel: "high", RequiresApproval: true, SuccessRate: 0.93},
			"revoke_credentials":  {ID: "revoke_credentials", Type: "identity", Description: "Revoke compromised credentials", RiskLevel: "medium", RequiresApproval: false, SuccessRate: 0.96},
			"update_firewall":     {ID: "update_firewall", Type: "network", Description: "Update firewall rules", RiskLevel: "low", RequiresApproval: false, SuccessRate: 0.98},
		},
		executionPolicy: ExecutionPolicy{
			AutoApproveThreshold: 0.90,
			MaxActionsPerHour:    50,
			CriticalActionsOnly:  false,
			BusinessHoursOnly:    false,
			ExcludedAssets:       []string{"critical-db-01", "payment-gateway"},
		},
		safetyLimits: SafetyLimits{
			MaxImpactedAssets:      10,
			MaxNetworkDisruption:   0.05,
			RollbackRequired:       true,
			HumanApprovalThreshold: 0.95,
		},
	}

	service := &Service{
		router:       router,
		aiEngine:     aiEngine,
		actionEngine: actionEngine,
		decisionLog:  make([]Decision, 0),
	}

	service.setupRoutes()
	return service
}

func (s *Service) setupRoutes() {
	// Health check
	s.router.GET("/health", s.healthHandler)

	// API routes
	api := s.router.Group("/api/v1")
	{
		// Autonomous decision making
		api.POST("/decide", s.makeDecisionHandler)
		api.POST("/incidents/:id/auto-respond", s.autoRespondHandler)

		// Decision log
		api.GET("/decisions", s.listDecisionsHandler)
		api.GET("/decisions/:id", s.getDecisionHandler)

		// ML models
		api.GET("/models", s.listModelsHandler)
		api.POST("/models/:name/train", s.trainModelHandler)

		// Actions
		api.GET("/actions", s.listActionsHandler)
		api.GET("/actions/:id/stats", s.getActionStatsHandler)

		// Policy management
		api.GET("/policy", s.getPolicyHandler)
		api.PUT("/policy", s.updatePolicyHandler)

		// Learning feedback
		api.POST("/feedback", s.submitFeedbackHandler)
	}

	// Metrics
	s.router.GET("/metrics", gin.WrapH(promhttp.Handler()))
}

func (s *Service) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"service": "ai-security-orchestrator",
		"timestamp": time.Now().Unix(),
		"models": len(s.aiEngine.models),
		"actions": len(s.actionEngine.actions),
	})
}

func (s *Service) makeDecisionHandler(c *gin.Context) {
	var req IncidentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	start := time.Now()
	recommendation := s.makeAutonomousDecision(req)
	decisionLatency.Observe(time.Since(start).Seconds())

	// Update metrics
	decisionsTotal.WithLabelValues(
		fmt.Sprintf("%t", recommendation.Decision.AutoExecuted),
		req.Severity,
	).Inc()
	confidenceScore.WithLabelValues(req.IncidentID).Set(recommendation.Decision.Confidence)

	c.JSON(http.StatusOK, recommendation)
}

func (s *Service) makeAutonomousDecision(req IncidentRequest) ResponseRecommendation {
	decision := Decision{
		ID:         fmt.Sprintf("decision-%d", time.Now().Unix()),
		Timestamp:  time.Now(),
		IncidentID: req.IncidentID,
		Severity:   req.Severity,
	}

	// Simulate AI analysis
	confidence := s.aiEngine.analyzeIncident(req)
	decision.Confidence = confidence

	// Determine recommended actions
	actions := s.selectOptimalActions(req, confidence)
	decision.RecommendedAction = actions[0].Type

	// Generate rationale
	decision.Rationale = fmt.Sprintf(
		"Analyzed %s severity incident with %d indicators. ML models (%.0f%% confidence) recommend %s",
		req.Severity,
		len(req.Indicators),
		confidence*100,
		decision.RecommendedAction,
	)

	// Auto-execute if confidence is high enough
	policy := s.actionEngine.executionPolicy
	if !req.RequireApproval && confidence >= policy.AutoApproveThreshold {
		decision.AutoExecuted = true
		decision.Outcome = "executed"
		s.executeActions(actions)
	} else {
		decision.AutoExecuted = false
		decision.Outcome = "awaiting_approval"
	}

	s.decisionLog = append(s.decisionLog, decision)

	// Predict impact
	impact := s.predictImpact(req, actions)

	return ResponseRecommendation{
		Decision:       decision,
		Actions:        actions,
		ImpactAnalysis: impact,
		ExecutionPlan:  s.generateExecutionPlan(actions),
		Alternatives:   s.generateAlternatives(req),
	}
}

func (ai *AIEngine) analyzeIncident(req IncidentRequest) float64 {
	// Simulate ML-based confidence scoring
	baseConfidence := 0.75

	// Increase confidence based on number of indicators
	indicatorBoost := float64(len(req.Indicators)) * 0.02
	if indicatorBoost > 0.15 {
		indicatorBoost = 0.15
	}

	// Severity adjustment
	severityBoost := 0.0
	switch req.Severity {
	case "critical":
		severityBoost = 0.10
	case "high":
		severityBoost = 0.05
	case "medium":
		severityBoost = 0.02
	}

	confidence := baseConfidence + indicatorBoost + severityBoost
	if confidence > 0.99 {
		confidence = 0.99
	}

	return confidence
}

func (s *Service) selectOptimalActions(req IncidentRequest, confidence float64) []Action {
	actions := make([]Action, 0)

	// Select actions based on threat type and confidence
	switch req.ThreatType {
	case "malware":
		actions = append(actions, s.actionEngine.actions["isolate_host"])
		actions = append(actions, s.actionEngine.actions["kill_process"])
	case "phishing":
		actions = append(actions, s.actionEngine.actions["quarantine_email"])
		actions = append(actions, s.actionEngine.actions["disable_account"])
	case "network_intrusion":
		actions = append(actions, s.actionEngine.actions["block_ip"])
		actions = append(actions, s.actionEngine.actions["update_firewall"])
	case "credential_compromise":
		actions = append(actions, s.actionEngine.actions["revoke_credentials"])
		actions = append(actions, s.actionEngine.actions["disable_account"])
	default:
		actions = append(actions, s.actionEngine.actions["isolate_host"])
	}

	return actions
}

func (s *Service) executeActions(actions []Action) {
	for _, action := range actions {
		log.Printf("Executing autonomous action: %s", action.ID)
		// Simulate action execution
		actionsExecuted.WithLabelValues(action.Type, "true").Inc()
	}
}

func (s *Service) predictImpact(req IncidentRequest, actions []Action) Impact {
	affectedSystems := len(req.AffectedAssets)
	for _, action := range actions {
		if action.Type == "network" || action.Type == "infrastructure" {
			affectedSystems += 5
		}
	}

	return Impact{
		AffectedSystems:   affectedSystems,
		ServiceDisruption: "minimal",
		DataLoss:          "none",
		ConfidenceLevel:   0.88,
	}
}

func (s *Service) generateExecutionPlan(actions []Action) string {
	plan := "Autonomous Execution Plan:\n"
	for i, action := range actions {
		plan += fmt.Sprintf("%d. %s - %s (Risk: %s)\n", i+1, action.Description, action.Type, action.RiskLevel)
	}
	return plan
}

func (s *Service) generateAlternatives(req IncidentRequest) []string {
	return []string{
		"Manual investigation with analyst review",
		"Gradual containment with monitoring",
		"Alert-only mode with enhanced logging",
	}
}

func (s *Service) autoRespondHandler(c *gin.Context) {
	incidentID := c.Param("id")

	var req IncidentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	req.IncidentID = incidentID

	recommendation := s.makeAutonomousDecision(req)

	c.JSON(http.StatusOK, gin.H{
		"incident_id": incidentID,
		"decision":    recommendation.Decision,
		"actions":     recommendation.Actions,
		"impact":      recommendation.ImpactAnalysis,
	})
}

func (s *Service) listDecisionsHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"decisions": s.decisionLog,
		"count":     len(s.decisionLog),
	})
}

func (s *Service) getDecisionHandler(c *gin.Context) {
	decisionID := c.Param("id")

	for _, decision := range s.decisionLog {
		if decision.ID == decisionID {
			c.JSON(http.StatusOK, decision)
			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "decision not found"})
}

func (s *Service) listModelsHandler(c *gin.Context) {
	models := make([]MLModel, 0)
	for _, model := range s.aiEngine.models {
		models = append(models, *model)
	}

	c.JSON(http.StatusOK, gin.H{
		"models": models,
		"count":  len(models),
	})
}

func (s *Service) trainModelHandler(c *gin.Context) {
	modelName := c.Param("name")

	if model, exists := s.aiEngine.models[modelName]; exists {
		model.LastTrained = time.Now()
		model.Accuracy += 0.01 // Simulate improvement

		c.JSON(http.StatusOK, gin.H{
			"status":       "training_started",
			"model":        modelName,
			"last_trained": model.LastTrained,
		})
	} else {
		c.JSON(http.StatusNotFound, gin.H{"error": "model not found"})
	}
}

func (s *Service) listActionsHandler(c *gin.Context) {
	actions := make([]Action, 0)
	for _, action := range s.actionEngine.actions {
		actions = append(actions, action)
	}

	c.JSON(http.StatusOK, gin.H{
		"actions": actions,
		"count":   len(actions),
	})
}

func (s *Service) getActionStatsHandler(c *gin.Context) {
	actionID := c.Param("id")

	if action, exists := s.actionEngine.actions[actionID]; exists {
		c.JSON(http.StatusOK, gin.H{
			"action":          action,
			"execution_count": action.ExecutionCount,
			"success_rate":    action.SuccessRate,
			"last_24h":        42, // Simulated
		})
	} else {
		c.JSON(http.StatusNotFound, gin.H{"error": "action not found"})
	}
}

func (s *Service) getPolicyHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"execution_policy": s.actionEngine.executionPolicy,
		"safety_limits":    s.actionEngine.safetyLimits,
	})
}

func (s *Service) updatePolicyHandler(c *gin.Context) {
	var policy ExecutionPolicy
	if err := c.ShouldBindJSON(&policy); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	s.actionEngine.executionPolicy = policy

	c.JSON(http.StatusOK, gin.H{
		"status": "updated",
		"policy": policy,
	})
}

func (s *Service) submitFeedbackHandler(c *gin.Context) {
	var feedback struct {
		DecisionID string  `json:"decision_id"`
		Effective  bool    `json:"effective"`
		Reward     float64 `json:"reward"`
		Notes      string  `json:"notes"`
	}

	if err := c.ShouldBindJSON(&feedback); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Update reinforcement learning model
	s.aiEngine.learningEngine.updateFromFeedback(feedback.DecisionID, feedback.Reward)

	c.JSON(http.StatusOK, gin.H{
		"status":  "feedback_recorded",
		"decision": feedback.DecisionID,
	})
}

func (rl *ReinforcementLearning) updateFromFeedback(stateAction string, reward float64) {
	currentValue := rl.StateActionValues[stateAction]
	rl.StateActionValues[stateAction] = currentValue + rl.LearningRate*(reward-currentValue)
}

func (s *Service) Start() error {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8085"
	}

	srv := &http.Server{
		Addr:    ":" + port,
		Handler: s.router,
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

	log.Printf("AI Security Orchestrator service starting on port %s", port)
	return srv.ListenAndServe()
}

func main() {
	service := NewService()
	if err := service.Start(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Failed to start service: %v", err)
	}
}
