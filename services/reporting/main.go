package main

import (
	"fmt"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	log "github.com/sirupsen/logrus"
)

type ReportType string

const (
	CompliancePCIDSS  ReportType = "pci-dss"
	ComplianceHIPAA   ReportType = "hipaa"
	ComplianceSOC2    ReportType = "soc2"
	ComplianceGDPR    ReportType = "gdpr"
	ComplianceISO27001 ReportType = "iso27001"
	SecuritySummary   ReportType = "security-summary"
	IncidentReport    ReportType = "incident-report"
)

type Report struct {
	ID          uuid.UUID  `json:"id"`
	Type        ReportType `json:"type"`
	Title       string     `json:"title"`
	StartDate   time.Time  `json:"start_date"`
	EndDate     time.Time  `json:"end_date"`
	GeneratedAt time.Time  `json:"generated_at"`
	GeneratedBy string     `json:"generated_by"`
	Status      string     `json:"status"`
	Format      string     `json:"format"`
	FilePath    string     `json:"file_path,omitempty"`
}

func main() {
	log.SetFormatter(&log.JSONFormatter{})
	log.Info("Starting Reporting Service")

	router := gin.Default()
	setupRoutes(router)

	port := getEnv("SERVER_PORT", "8085")
	log.Infof("Starting server on :%s", port)
	router.Run(":" + port)
}

func setupRoutes(router *gin.Engine) {
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "healthy", "service": "reporting"})
	})

	v1 := router.Group("/api/v1")
	{
		reports := v1.Group("/reports")
		{
			reports.GET("", listReports)
			reports.POST("", generateReport)
			reports.GET("/:id", getReport)
			reports.GET("/:id/download", downloadReport)
		}

		templates := v1.Group("/templates")
		{
			templates.GET("", listTemplates)
			templates.GET("/:type", getTemplate)
		}
	}
}

func listReports(c *gin.Context) {
	c.JSON(200, gin.H{"reports": []Report{}})
}

func generateReport(c *gin.Context) {
	var req struct {
		Type      ReportType `json:"type"`
		StartDate time.Time  `json:"start_date"`
		EndDate   time.Time  `json:"end_date"`
		Format    string     `json:"format"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	report := Report{
		ID:          uuid.New(),
		Type:        req.Type,
		Title:       fmt.Sprintf("%s Report", req.Type),
		StartDate:   req.StartDate,
		EndDate:     req.EndDate,
		GeneratedAt: time.Now(),
		GeneratedBy: "system",
		Status:      "completed",
		Format:      req.Format,
	}

	c.JSON(201, report)
}

func getReport(c *gin.Context) {
	c.JSON(200, gin.H{"id": c.Param("id")})
}

func downloadReport(c *gin.Context) {
	c.JSON(200, gin.H{"download_url": "/reports/" + c.Param("id") + "/file.pdf"})
}

func listTemplates(c *gin.Context) {
	templates := []gin.H{
		{"type": CompliancePCIDSS, "name": "PCI-DSS Compliance Report", "description": "Payment Card Industry Data Security Standard"},
		{"type": ComplianceHIPAA, "name": "HIPAA Compliance Report", "description": "Health Insurance Portability and Accountability Act"},
		{"type": ComplianceSOC2, "name": "SOC 2 Compliance Report", "description": "Service Organization Control 2"},
		{"type": ComplianceGDPR, "name": "GDPR Compliance Report", "description": "General Data Protection Regulation"},
		{"type": ComplianceISO27001, "name": "ISO 27001 Compliance Report", "description": "Information Security Management"},
		{"type": SecuritySummary, "name": "Security Summary Report", "description": "Overall security posture"},
		{"type": IncidentReport, "name": "Incident Report", "description": "Detailed incident analysis"},
	}
	c.JSON(200, gin.H{"templates": templates})
}

func getTemplate(c *gin.Context) {
	c.JSON(200, gin.H{"type": c.Param("type"), "template": "Template content here"})
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
