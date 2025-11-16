package notification

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/enterprise-siem/alert-manager/internal/config"
	"github.com/enterprise-siem/alert-manager/internal/models"
	log "github.com/sirupsen/logrus"
)

type Service struct {
	config config.NotificationConfig
}

func New(cfg config.NotificationConfig) *Service {
	return &Service{config: cfg}
}

func (s *Service) NotifyAlert(alert *models.Alert) {
	log.WithFields(log.Fields{
		"alert_id": alert.ID,
		"severity": alert.Severity,
	}).Info("Sending alert notifications")

	if s.config.SlackWebhook != "" {
		if err := s.sendSlackNotification(alert); err != nil {
			log.Errorf("Failed to send Slack notification: %v", err)
		}
	}

	if s.config.TeamsWebhook != "" {
		if err := s.sendTeamsNotification(alert); err != nil {
			log.Errorf("Failed to send Teams notification: %v", err)
		}
	}

	if s.config.EmailEnabled {
		if err := s.sendEmailNotification(alert); err != nil {
			log.Errorf("Failed to send email notification: %v", err)
		}
	}
}

func (s *Service) sendSlackNotification(alert *models.Alert) error {
	color := s.getSeverityColor(alert.Severity)

	payload := map[string]interface{}{
		"attachments": []map[string]interface{}{
			{
				"color":  color,
				"title":  fmt.Sprintf("[%s] %s", alert.Severity, alert.Title),
				"text":   alert.Description,
				"footer": fmt.Sprintf("Alert ID: %s", alert.ID),
				"ts":     alert.CreatedAt.Unix(),
				"fields": []map[string]interface{}{
					{
						"title": "Severity",
						"value": string(alert.Severity),
						"short": true,
					},
					{
						"title": "Status",
						"value": string(alert.Status),
						"short": true,
					},
				},
			},
		},
	}

	return s.sendWebhook(s.config.SlackWebhook, payload)
}

func (s *Service) sendTeamsNotification(alert *models.Alert) error {
	color := s.getSeverityColor(alert.Severity)

	payload := map[string]interface{}{
		"@type":      "MessageCard",
		"@context":   "https://schema.org/extensions",
		"summary":    alert.Title,
		"themeColor": color,
		"title":      fmt.Sprintf("[%s] %s", alert.Severity, alert.Title),
		"text":       alert.Description,
		"sections": []map[string]interface{}{
			{
				"facts": []map[string]interface{}{
					{"name": "Severity", "value": string(alert.Severity)},
					{"name": "Status", "value": string(alert.Status)},
					{"name": "Alert ID", "value": alert.ID.String()},
				},
			},
		},
	}

	return s.sendWebhook(s.config.TeamsWebhook, payload)
}

func (s *Service) sendEmailNotification(alert *models.Alert) error {
	// Simplified - would use proper SMTP library
	log.Info("Email notification would be sent here")
	return nil
}

func (s *Service) sendWebhook(url string, payload interface{}) error {
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("webhook returned status %d", resp.StatusCode)
	}

	return nil
}

func (s *Service) getSeverityColor(severity models.Severity) string {
	switch severity {
	case models.SeverityCritical:
		return "#FF0000"
	case models.SeverityHigh:
		return "#FF6600"
	case models.SeverityMedium:
		return "#FFCC00"
	case models.SeverityLow:
		return "#00CC00"
	default:
		return "#808080"
	}
}
