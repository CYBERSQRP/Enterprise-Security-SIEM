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
	"github.com/gorilla/websocket"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// CollaborationHub manages real-time collaboration features
type CollaborationHub struct {
	config          *Config
	sessions        map[string]*InvestigationSession
	sessionsMu      sync.RWMutex
	chatService     *ChatService
	annotationService *AnnotationService
	httpServer      *http.Server
	metricsServer   *http.Server
	upgrader        websocket.Upgrader
	metricsCollector *MetricsCollector
}

// Config holds the service configuration
type Config struct {
	Port              string
	MetricsPort       string
	RedisAddr         string
	PostgresURL       string
	MaxSessionSize    int
	MessageRetention  time.Duration
}

// InvestigationSession represents a collaborative investigation session
type InvestigationSession struct {
	ID              string                 `json:"id"`
	IncidentID      string                 `json:"incident_id"`
	Name            string                 `json:"name"`
	CreatedBy       string                 `json:"created_by"`
	CreatedAt       time.Time              `json:"created_at"`
	Participants    map[string]*Participant `json:"participants"`
	participantsMu  sync.RWMutex
	Messages        []*ChatMessage         `json:"messages"`
	messagesMu      sync.RWMutex
	Annotations     []*Annotation          `json:"annotations"`
	annotationsMu   sync.RWMutex
	Active          bool                   `json:"active"`
	broadcast       chan *BroadcastMessage
	register        chan *Participant
	unregister      chan *Participant
}

// Participant represents a user in an investigation session
type Participant struct {
	UserID      string          `json:"user_id"`
	Username    string          `json:"username"`
	Role        string          `json:"role"` // analyst, lead, observer
	JoinedAt    time.Time       `json:"joined_at"`
	CursorPos   *CursorPosition `json:"cursor_pos,omitempty"`
	Connection  *websocket.Conn `json:"-"`
	Send        chan []byte     `json:"-"`
}

// CursorPosition tracks user cursor position
type CursorPosition struct {
	X         int       `json:"x"`
	Y         int       `json:"y"`
	Timestamp time.Time `json:"timestamp"`
}

// ChatMessage represents a chat message in a session
type ChatMessage struct {
	ID          string    `json:"id"`
	SessionID   string    `json:"session_id"`
	UserID      string    `json:"user_id"`
	Username    string    `json:"username"`
	Content     string    `json:"content"`
	Timestamp   time.Time `json:"timestamp"`
	Mentions    []string  `json:"mentions,omitempty"`
	ThreadID    string    `json:"thread_id,omitempty"`
	Attachments []string  `json:"attachments,omitempty"`
}

// Annotation represents an annotation on an event or evidence
type Annotation struct {
	ID          string            `json:"id"`
	SessionID   string            `json:"session_id"`
	TargetType  string            `json:"target_type"` // event, evidence, timeline
	TargetID    string            `json:"target_id"`
	UserID      string            `json:"user_id"`
	Username    string            `json:"username"`
	Content     string            `json:"content"`
	Timestamp   time.Time         `json:"timestamp"`
	Tags        []string          `json:"tags"`
	Metadata    map[string]string `json:"metadata,omitempty"`
}

// BroadcastMessage represents a message to broadcast to all participants
type BroadcastMessage struct {
	Type    string      `json:"type"` // chat, annotation, cursor, event
	Payload interface{} `json:"payload"`
}

// ChatService manages chat functionality
type ChatService struct {
	messages   map[string][]*ChatMessage
	messagesMu sync.RWMutex
}

// AnnotationService manages annotations
type AnnotationService struct {
	annotations   map[string][]*Annotation
	annotationsMu sync.RWMutex
}

// MetricsCollector collects Prometheus metrics
type MetricsCollector struct {
	ActiveSessions      prometheus.Gauge
	TotalParticipants   prometheus.Gauge
	MessagesProcessed   prometheus.Counter
	AnnotationsCreated  prometheus.Counter
	WebSocketConnections prometheus.Gauge
	SessionDuration     prometheus.Histogram
}

func NewMetricsCollector() *MetricsCollector {
	mc := &MetricsCollector{
		ActiveSessions: prometheus.NewGauge(prometheus.GaugeOpts{
			Name: "collaboration_active_sessions",
			Help: "Number of active investigation sessions",
		}),
		TotalParticipants: prometheus.NewGauge(prometheus.GaugeOpts{
			Name: "collaboration_total_participants",
			Help: "Total number of participants across all sessions",
		}),
		MessagesProcessed: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "collaboration_messages_processed_total",
			Help: "Total number of chat messages processed",
		}),
		AnnotationsCreated: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "collaboration_annotations_created_total",
			Help: "Total number of annotations created",
		}),
		WebSocketConnections: prometheus.NewGauge(prometheus.GaugeOpts{
			Name: "collaboration_websocket_connections",
			Help: "Number of active WebSocket connections",
		}),
		SessionDuration: prometheus.NewHistogram(prometheus.HistogramOpts{
			Name:    "collaboration_session_duration_seconds",
			Help:    "Duration of investigation sessions",
			Buckets: prometheus.DefBuckets,
		}),
	}

	prometheus.MustRegister(mc.ActiveSessions)
	prometheus.MustRegister(mc.TotalParticipants)
	prometheus.MustRegister(mc.MessagesProcessed)
	prometheus.MustRegister(mc.AnnotationsCreated)
	prometheus.MustRegister(mc.WebSocketConnections)
	prometheus.MustRegister(mc.SessionDuration)

	return mc
}

func NewCollaborationHub(config *Config) *CollaborationHub {
	return &CollaborationHub{
		config:   config,
		sessions: make(map[string]*InvestigationSession),
		chatService: &ChatService{
			messages: make(map[string][]*ChatMessage),
		},
		annotationService: &AnnotationService{
			annotations: make(map[string][]*Annotation),
		},
		upgrader: websocket.Upgrader{
			ReadBufferSize:  1024,
			WriteBufferSize: 1024,
			CheckOrigin: func(r *http.Request) bool {
				return true // In production, check origin properly
			},
		},
		metricsCollector: NewMetricsCollector(),
	}
}

func (h *CollaborationHub) Start(ctx context.Context) error {
	log.Println("Starting Collaboration Hub...")

	// Start HTTP API server
	if err := h.startHTTPServer(); err != nil {
		return fmt.Errorf("failed to start HTTP server: %w", err)
	}

	// Start metrics server
	if err := h.startMetricsServer(); err != nil {
		return fmt.Errorf("failed to start metrics server: %w", err)
	}

	// Start background workers
	go h.metricsUpdater(ctx)

	log.Println("Collaboration Hub started successfully")
	return nil
}

func (h *CollaborationHub) startHTTPServer() error {
	router := mux.NewRouter()

	// API routes
	router.HandleFunc("/health", h.healthHandler).Methods("GET")
	router.HandleFunc("/ready", h.readyHandler).Methods("GET")
	router.HandleFunc("/api/v1/sessions", h.listSessionsHandler).Methods("GET")
	router.HandleFunc("/api/v1/sessions", h.createSessionHandler).Methods("POST")
	router.HandleFunc("/api/v1/sessions/{id}", h.getSessionHandler).Methods("GET")
	router.HandleFunc("/api/v1/sessions/{id}/join", h.joinSessionHandler).Methods("POST")
	router.HandleFunc("/api/v1/sessions/{id}/messages", h.getMessagesHandler).Methods("GET")
	router.HandleFunc("/api/v1/sessions/{id}/annotations", h.getAnnotationsHandler).Methods("GET")

	// WebSocket route
	router.HandleFunc("/ws/sessions/{id}", h.websocketHandler)

	h.httpServer = &http.Server{
		Addr:         ":" + h.config.Port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		log.Printf("HTTP API server listening on :%s", h.config.Port)
		if err := h.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	return nil
}

func (h *CollaborationHub) startMetricsServer() error {
	metricsRouter := mux.NewRouter()
	metricsRouter.Handle("/metrics", promhttp.Handler())

	h.metricsServer = &http.Server{
		Addr:    ":" + h.config.MetricsPort,
		Handler: metricsRouter,
	}

	go func() {
		log.Printf("Metrics server listening on :%s", h.config.MetricsPort)
		if err := h.metricsServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Metrics server error: %v", err)
		}
	}()

	return nil
}

func (h *CollaborationHub) metricsUpdater(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			h.updateMetrics()
		}
	}
}

func (h *CollaborationHub) updateMetrics() {
	h.sessionsMu.RLock()
	defer h.sessionsMu.RUnlock()

	activeSessions := 0
	totalParticipants := 0

	for _, session := range h.sessions {
		if session.Active {
			activeSessions++
			session.participantsMu.RLock()
			totalParticipants += len(session.Participants)
			session.participantsMu.RUnlock()
		}
	}

	h.metricsCollector.ActiveSessions.Set(float64(activeSessions))
	h.metricsCollector.TotalParticipants.Set(float64(totalParticipants))
}

func (h *CollaborationHub) createSession(incidentID, name, createdBy string) *InvestigationSession {
	session := &InvestigationSession{
		ID:           fmt.Sprintf("session-%d", time.Now().Unix()),
		IncidentID:   incidentID,
		Name:         name,
		CreatedBy:    createdBy,
		CreatedAt:    time.Now(),
		Participants: make(map[string]*Participant),
		Messages:     make([]*ChatMessage, 0),
		Annotations:  make([]*Annotation, 0),
		Active:       true,
		broadcast:    make(chan *BroadcastMessage, 256),
		register:     make(chan *Participant),
		unregister:   make(chan *Participant),
	}

	// Start session manager
	go session.run()

	h.sessionsMu.Lock()
	h.sessions[session.ID] = session
	h.sessionsMu.Unlock()

	log.Printf("Created session: %s for incident %s", session.ID, incidentID)
	return session
}

func (s *InvestigationSession) run() {
	for {
		select {
		case participant := <-s.register:
			s.participantsMu.Lock()
			s.Participants[participant.UserID] = participant
			s.participantsMu.Unlock()
			log.Printf("Participant %s joined session %s", participant.Username, s.ID)

		case participant := <-s.unregister:
			s.participantsMu.Lock()
			if _, ok := s.Participants[participant.UserID]; ok {
				delete(s.Participants, participant.UserID)
				close(participant.Send)
			}
			s.participantsMu.Unlock()
			log.Printf("Participant %s left session %s", participant.Username, s.ID)

		case message := <-s.broadcast:
			s.participantsMu.RLock()
			for _, participant := range s.Participants {
				select {
				case participant.Send <- mustMarshal(message):
				default:
					close(participant.Send)
					delete(s.Participants, participant.UserID)
				}
			}
			s.participantsMu.RUnlock()
		}
	}
}

func (h *CollaborationHub) websocketHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	h.sessionsMu.RLock()
	session, exists := h.sessions[sessionID]
	h.sessionsMu.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	// Upgrade to WebSocket
	conn, err := h.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	// Create participant
	participant := &Participant{
		UserID:     r.URL.Query().Get("user_id"),
		Username:   r.URL.Query().Get("username"),
		Role:       "analyst",
		JoinedAt:   time.Now(),
		Connection: conn,
		Send:       make(chan []byte, 256),
	}

	session.register <- participant
	h.metricsCollector.WebSocketConnections.Inc()

	// Start read/write pumps
	go h.writePump(participant)
	go h.readPump(session, participant)
}

func (h *CollaborationHub) readPump(session *InvestigationSession, participant *Participant) {
	defer func() {
		session.unregister <- participant
		participant.Connection.Close()
		h.metricsCollector.WebSocketConnections.Dec()
	}()

	for {
		var msg map[string]interface{}
		err := participant.Connection.ReadJSON(&msg)
		if err != nil {
			break
		}

		msgType, ok := msg["type"].(string)
		if !ok {
			continue
		}

		switch msgType {
		case "chat":
			h.handleChatMessage(session, participant, msg)
		case "annotation":
			h.handleAnnotation(session, participant, msg)
		case "cursor":
			h.handleCursorUpdate(session, participant, msg)
		}
	}
}

func (h *CollaborationHub) writePump(participant *Participant) {
	for {
		message, ok := <-participant.Send
		if !ok {
			participant.Connection.WriteMessage(websocket.CloseMessage, []byte{})
			return
		}

		if err := participant.Connection.WriteMessage(websocket.TextMessage, message); err != nil {
			return
		}
	}
}

func (h *CollaborationHub) handleChatMessage(session *InvestigationSession, participant *Participant, msg map[string]interface{}) {
	content, _ := msg["content"].(string)

	chatMsg := &ChatMessage{
		ID:        fmt.Sprintf("msg-%d", time.Now().UnixNano()),
		SessionID: session.ID,
		UserID:    participant.UserID,
		Username:  participant.Username,
		Content:   content,
		Timestamp: time.Now(),
	}

	session.messagesMu.Lock()
	session.Messages = append(session.Messages, chatMsg)
	session.messagesMu.Unlock()

	h.metricsCollector.MessagesProcessed.Inc()

	// Broadcast to all participants
	session.broadcast <- &BroadcastMessage{
		Type:    "chat",
		Payload: chatMsg,
	}
}

func (h *CollaborationHub) handleAnnotation(session *InvestigationSession, participant *Participant, msg map[string]interface{}) {
	payload, _ := msg["payload"].(map[string]interface{})
	targetType, _ := payload["target_type"].(string)
	targetID, _ := payload["target_id"].(string)
	content, _ := payload["content"].(string)

	annotation := &Annotation{
		ID:         fmt.Sprintf("ann-%d", time.Now().UnixNano()),
		SessionID:  session.ID,
		TargetType: targetType,
		TargetID:   targetID,
		UserID:     participant.UserID,
		Username:   participant.Username,
		Content:    content,
		Timestamp:  time.Now(),
	}

	session.annotationsMu.Lock()
	session.Annotations = append(session.Annotations, annotation)
	session.annotationsMu.Unlock()

	h.metricsCollector.AnnotationsCreated.Inc()

	// Broadcast to all participants
	session.broadcast <- &BroadcastMessage{
		Type:    "annotation",
		Payload: annotation,
	}
}

func (h *CollaborationHub) handleCursorUpdate(session *InvestigationSession, participant *Participant, msg map[string]interface{}) {
	payload, _ := msg["payload"].(map[string]interface{})
	x, _ := payload["x"].(float64)
	y, _ := payload["y"].(float64)

	participant.CursorPos = &CursorPosition{
		X:         int(x),
		Y:         int(y),
		Timestamp: time.Now(),
	}

	// Broadcast cursor position to other participants
	session.broadcast <- &BroadcastMessage{
		Type: "cursor",
		Payload: map[string]interface{}{
			"user_id":  participant.UserID,
			"username": participant.Username,
			"x":        x,
			"y":        y,
		},
	}
}

// HTTP Handlers

func (h *CollaborationHub) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func (h *CollaborationHub) readyHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"status": "ready"})
}

func (h *CollaborationHub) listSessionsHandler(w http.ResponseWriter, r *http.Request) {
	h.sessionsMu.RLock()
	defer h.sessionsMu.RUnlock()

	sessions := make([]map[string]interface{}, 0, len(h.sessions))
	for _, session := range h.sessions {
		session.participantsMu.RLock()
		participantCount := len(session.Participants)
		session.participantsMu.RUnlock()

		sessions = append(sessions, map[string]interface{}{
			"id":                session.ID,
			"incident_id":       session.IncidentID,
			"name":              session.Name,
			"created_by":        session.CreatedBy,
			"created_at":        session.CreatedAt,
			"active":            session.Active,
			"participant_count": participantCount,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"sessions": sessions,
		"count":    len(sessions),
	})
}

func (h *CollaborationHub) createSessionHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		IncidentID string `json:"incident_id"`
		Name       string `json:"name"`
		CreatedBy  string `json:"created_by"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	session := h.createSession(req.IncidentID, req.Name, req.CreatedBy)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(session)
}

func (h *CollaborationHub) getSessionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	h.sessionsMu.RLock()
	session, exists := h.sessions[sessionID]
	h.sessionsMu.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(session)
}

func (h *CollaborationHub) joinSessionHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	var req struct {
		UserID   string `json:"user_id"`
		Username string `json:"username"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	h.sessionsMu.RLock()
	session, exists := h.sessions[sessionID]
	h.sessionsMu.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"session_id":     session.ID,
		"websocket_url":  fmt.Sprintf("ws://localhost:%s/ws/sessions/%s", h.config.Port, session.ID),
		"status":         "ready",
	})
}

func (h *CollaborationHub) getMessagesHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	h.sessionsMu.RLock()
	session, exists := h.sessions[sessionID]
	h.sessionsMu.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	session.messagesMu.RLock()
	messages := session.Messages
	session.messagesMu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"messages": messages,
		"count":    len(messages),
	})
}

func (h *CollaborationHub) getAnnotationsHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	sessionID := vars["id"]

	h.sessionsMu.RLock()
	session, exists := h.sessions[sessionID]
	h.sessionsMu.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	session.annotationsMu.RLock()
	annotations := session.Annotations
	session.annotationsMu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"annotations": annotations,
		"count":       len(annotations),
	})
}

func (h *CollaborationHub) Shutdown(ctx context.Context) error {
	log.Println("Shutting down Collaboration Hub...")

	if h.httpServer != nil {
		if err := h.httpServer.Shutdown(ctx); err != nil {
			log.Printf("Error shutting down HTTP server: %v", err)
			return err
		}
	}

	if h.metricsServer != nil {
		if err := h.metricsServer.Shutdown(ctx); err != nil {
			log.Printf("Error shutting down metrics server: %v", err)
			return err
		}
	}

	log.Println("Collaboration Hub shutdown complete")
	return nil
}

func mustMarshal(v interface{}) []byte {
	data, err := json.Marshal(v)
	if err != nil {
		log.Printf("JSON marshal error: %v", err)
		return []byte("{}")
	}
	return data
}

func main() {
	config := &Config{
		Port:             getEnv("PORT", "8083"),
		MetricsPort:      getEnv("METRICS_PORT", "9093"),
		RedisAddr:        getEnv("REDIS_ADDR", "localhost:6379"),
		PostgresURL:      getEnv("POSTGRES_URL", "postgresql://localhost:5432/siem"),
		MaxSessionSize:   50,
		MessageRetention: 30 * 24 * time.Hour, // 30 days
	}

	hub := NewCollaborationHub(config)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := hub.Start(ctx); err != nil {
		log.Fatalf("Failed to start hub: %v", err)
	}

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	log.Println("Received shutdown signal")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := hub.Shutdown(shutdownCtx); err != nil {
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
