package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/elastic/go-elasticsearch/v8"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type APIGateway struct {
	esClient *elasticsearch.Client
	config   *Config
	router   *gin.Engine
}

type Config struct {
	Port             int
	ElasticsearchURL string
}

type SearchRequest struct {
	Query  interface{} `json:"query"`
	From   int         `json:"from"`
	Size   int         `json:"size"`
	Sort   interface{} `json:"sort,omitempty"`
}

type SearchResponse struct {
	Total int           `json:"total"`
	Hits  []interface{} `json:"hits"`
}

type ErrorResponse struct {
	Error ErrorDetail `json:"error"`
}

type ErrorDetail struct {
	Code      string      `json:"code"`
	Message   string      `json:"message"`
	Details   interface{} `json:"details,omitempty"`
	RequestID string      `json:"request_id"`
	Timestamp time.Time   `json:"timestamp"`
}

func main() {
	config := &Config{
		Port:             getEnvInt("PORT", 8080),
		ElasticsearchURL: getEnv("ELASTICSEARCH_URL", "http://localhost:9200"),
	}

	gateway, err := NewAPIGateway(config)
	if err != nil {
		log.Fatalf("Failed to create API gateway: %v", err)
	}

	gateway.setupRoutes()

	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", config.Port),
		Handler: gateway.router,
	}

	go func() {
		log.Printf("API Gateway starting on port %d", config.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down API Gateway...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Printf("Server shutdown error: %v", err)
	}
}

func NewAPIGateway(config *Config) (*APIGateway, error) {
	esCfg := elasticsearch.Config{
		Addresses: []string{config.ElasticsearchURL},
	}
	esClient, err := elasticsearch.NewClient(esCfg)
	if err != nil {
		return nil, err
	}

	router := gin.Default()

	return &APIGateway{
		esClient: esClient,
		config:   config,
		router:   router,
	}, nil
}

func (gw *APIGateway) setupRoutes() {
	// Health check
	gw.router.GET("/health", gw.healthCheck)

	// API v1
	v1 := gw.router.Group("/api/v1")
	{
		// Events API
		events := v1.Group("/events")
		{
			events.POST("/search", gw.searchEvents)
			events.GET("/:event_id", gw.getEvent)
		}

		// Alerts API
		alerts := v1.Group("/alerts")
		{
			alerts.GET("", gw.listAlerts)
			alerts.GET("/:alert_id", gw.getAlert)
			alerts.POST("", gw.createAlert)
			alerts.PATCH("/:alert_id", gw.updateAlert)
		}

		// System stats
		v1.GET("/stats", gw.getStats)
	}
}

func (gw *APIGateway) healthCheck(c *gin.Context) {
	res, err := gw.esClient.Info()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"status": "unhealthy",
			"error":  err.Error(),
		})
		return
	}
	defer res.Body.Close()

	c.JSON(http.StatusOK, gin.H{
		"status":        "healthy",
		"elasticsearch": res.StatusCode == 200,
	})
}

func (gw *APIGateway) searchEvents(c *gin.Context) {
	var searchReq SearchRequest
	if err := c.ShouldBindJSON(&searchReq); err != nil {
		gw.sendError(c, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid request body", err.Error())
		return
	}

	// Default pagination
	if searchReq.Size == 0 {
		searchReq.Size = 100
	}

	// Build Elasticsearch query
	var buf bytes.Buffer
	if err := json.NewEncoder(&buf).Encode(searchReq); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "ENCODING_ERROR", "Failed to encode query", nil)
		return
	}

	// Search in Elasticsearch
	res, err := gw.esClient.Search(
		gw.esClient.Search.WithIndex("events-*"),
		gw.esClient.Search.WithBody(&buf),
	)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "SEARCH_ERROR", "Failed to search events", err.Error())
		return
	}
	defer res.Body.Close()

	// Parse response
	var esResponse map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&esResponse); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "DECODE_ERROR", "Failed to decode response", nil)
		return
	}

	// Extract hits
	hits := []interface{}{}
	total := 0

	if hitsData, ok := esResponse["hits"].(map[string]interface{}); ok {
		if totalData, ok := hitsData["total"].(map[string]interface{}); ok {
			if value, ok := totalData["value"].(float64); ok {
				total = int(value)
			}
		}
		if hitsArray, ok := hitsData["hits"].([]interface{}); ok {
			for _, hit := range hitsArray {
				if hitMap, ok := hit.(map[string]interface{}); ok {
					if source, ok := hitMap["_source"]; ok {
						hits = append(hits, source)
					}
				}
			}
		}
	}

	c.JSON(http.StatusOK, SearchResponse{
		Total: total,
		Hits:  hits,
	})
}

func (gw *APIGateway) getEvent(c *gin.Context) {
	eventID := c.Param("event_id")

	res, err := gw.esClient.Get("events-*", eventID)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "GET_ERROR", "Failed to get event", err.Error())
		return
	}
	defer res.Body.Close()

	if res.StatusCode == 404 {
		gw.sendError(c, http.StatusNotFound, "NOT_FOUND", "Event not found", nil)
		return
	}

	var result map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&result); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "DECODE_ERROR", "Failed to decode response", nil)
		return
	}

	if source, ok := result["_source"]; ok {
		c.JSON(http.StatusOK, source)
	} else {
		gw.sendError(c, http.StatusNotFound, "NOT_FOUND", "Event not found", nil)
	}
}

func (gw *APIGateway) listAlerts(c *gin.Context) {
	// Build query for alerts
	query := map[string]interface{}{
		"query": map[string]interface{}{
			"match_all": map[string]interface{}{},
		},
		"size": 50,
		"sort": []map[string]interface{}{
			{"timestamp": map[string]string{"order": "desc"}},
		},
	}

	var buf bytes.Buffer
	if err := json.NewEncoder(&buf).Encode(query); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "ENCODING_ERROR", "Failed to encode query", nil)
		return
	}

	res, err := gw.esClient.Search(
		gw.esClient.Search.WithIndex("alerts-*"),
		gw.esClient.Search.WithBody(&buf),
	)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "SEARCH_ERROR", "Failed to search alerts", err.Error())
		return
	}
	defer res.Body.Close()

	var esResponse map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&esResponse); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "DECODE_ERROR", "Failed to decode response", nil)
		return
	}

	c.JSON(http.StatusOK, esResponse)
}

func (gw *APIGateway) getAlert(c *gin.Context) {
	alertID := c.Param("alert_id")

	res, err := gw.esClient.Get("alerts-*", alertID)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "GET_ERROR", "Failed to get alert", err.Error())
		return
	}
	defer res.Body.Close()

	if res.StatusCode == 404 {
		gw.sendError(c, http.StatusNotFound, "NOT_FOUND", "Alert not found", nil)
		return
	}

	var result map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&result); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "DECODE_ERROR", "Failed to decode response", nil)
		return
	}

	if source, ok := result["_source"]; ok {
		c.JSON(http.StatusOK, source)
	} else {
		gw.sendError(c, http.StatusNotFound, "NOT_FOUND", "Alert not found", nil)
	}
}

func (gw *APIGateway) createAlert(c *gin.Context) {
	var alert map[string]interface{}
	if err := c.ShouldBindJSON(&alert); err != nil {
		gw.sendError(c, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid request body", err.Error())
		return
	}

	// Add metadata
	alertID := uuid.New().String()
	alert["alert_id"] = alertID
	alert["timestamp"] = time.Now().UTC()
	alert["status"] = "new"
	alert["created_at"] = time.Now().UTC()
	alert["updated_at"] = time.Now().UTC()

	// Index to Elasticsearch
	var buf bytes.Buffer
	if err := json.NewEncoder(&buf).Encode(alert); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "ENCODING_ERROR", "Failed to encode alert", nil)
		return
	}

	indexName := "alerts-" + time.Now().Format("2006.01")
	res, err := gw.esClient.Index(
		indexName,
		&buf,
		gw.esClient.Index.WithDocumentID(alertID),
		gw.esClient.Index.WithRefresh("true"),
	)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "INDEX_ERROR", "Failed to create alert", err.Error())
		return
	}
	defer res.Body.Close()

	c.JSON(http.StatusCreated, alert)
}

func (gw *APIGateway) updateAlert(c *gin.Context) {
	alertID := c.Param("alert_id")

	var updates map[string]interface{}
	if err := c.ShouldBindJSON(&updates); err != nil {
		gw.sendError(c, http.StatusBadRequest, "VALIDATION_ERROR", "Invalid request body", err.Error())
		return
	}

	updates["updated_at"] = time.Now().UTC()

	// Update document
	updateDoc := map[string]interface{}{
		"doc": updates,
	}

	var buf bytes.Buffer
	if err := json.NewEncoder(&buf).Encode(updateDoc); err != nil {
		gw.sendError(c, http.StatusInternalServerError, "ENCODING_ERROR", "Failed to encode update", nil)
		return
	}

	res, err := gw.esClient.Update("alerts-*", alertID, &buf)
	if err != nil {
		gw.sendError(c, http.StatusInternalServerError, "UPDATE_ERROR", "Failed to update alert", err.Error())
		return
	}
	defer res.Body.Close()

	if res.StatusCode == 404 {
		gw.sendError(c, http.StatusNotFound, "NOT_FOUND", "Alert not found", nil)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"alert_id":   alertID,
		"updated_at": updates["updated_at"],
		"message":    "Alert updated successfully",
	})
}

func (gw *APIGateway) getStats(c *gin.Context) {
	stats := gin.H{
		"status":    "operational",
		"version":   "1.0.0",
		"timestamp": time.Now().UTC(),
	}

	c.JSON(http.StatusOK, stats)
}

func (gw *APIGateway) sendError(c *gin.Context, status int, code, message string, details interface{}) {
	c.JSON(status, ErrorResponse{
		Error: ErrorDetail{
			Code:      code,
			Message:   message,
			Details:   details,
			RequestID: uuid.New().String(),
			Timestamp: time.Now().UTC(),
		},
	})
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
