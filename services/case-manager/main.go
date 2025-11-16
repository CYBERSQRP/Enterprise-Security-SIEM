package main

import (
	"database/sql"
	"fmt"
	"os"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
	log "github.com/sirupsen/logrus"
)

func main() {
	log.SetFormatter(&log.JSONFormatter{})
	log.Info("Starting Case Manager Service")

	dbURL := getEnv("DATABASE_URL", "postgresql://siem:siem@postgres:5432/siem")
	db, err := sql.Open("postgres", dbURL)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	router := gin.Default()
	setupRoutes(router, db)

	port := getEnv("SERVER_PORT", "8083")
	log.Infof("Starting server on :%s", port)
	router.Run(":" + port)
}

func setupRoutes(router *gin.Engine, db *sql.DB) {
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "case-manager"})
	})

	v1 := router.Group("/api/v1")
	{
		cases := v1.Group("/cases")
		{
			cases.GET("", listCases)
			cases.POST("", createCase)
			cases.GET("/:id", getCase)
			cases.PATCH("/:id", updateCase)
			cases.POST("/:id/evidence", addEvidence)
			cases.GET("/:id/timeline", getTimeline)
			cases.POST("/:id/comments", addComment)
		}
	}
}

func listCases(c *gin.Context) {
	c.JSON(200, gin.H{"cases": []interface{}{}})
}

func createCase(c *gin.Context) {
	c.JSON(201, gin.H{"status": "created"})
}

func getCase(c *gin.Context) {
	c.JSON(200, gin.H{"id": c.Param("id")})
}

func updateCase(c *gin.Context) {
	c.JSON(200, gin.H{"status": "updated"})
}

func addEvidence(c *gin.Context) {
	c.JSON(201, gin.H{"status": "evidence added"})
}

func getTimeline(c *gin.Context) {
	c.JSON(200, gin.H{"timeline": []interface{}{}})
}

func addComment(c *gin.Context) {
	c.JSON(201, gin.H{"status": "comment added"})
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
