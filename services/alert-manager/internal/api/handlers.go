package api

import (
	"net/http"
	"time"

	"github.com/enterprise-siem/alert-manager/internal/models"
	"github.com/enterprise-siem/alert-manager/internal/notification"
	"github.com/enterprise-siem/alert-manager/internal/storage"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

func listAlertsHandler(store *storage.Storage) gin.HandlerFunc {
	return func(c *gin.Context) {
		filter := &models.AlertFilter{
			Limit:  50,
			Offset: 0,
		}

		// Parse query parameters
		// (simplified - would need proper query param parsing)

		alerts, err := store.ListAlerts(c.Request.Context(), filter)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{"alerts": alerts})
	}
}

func createAlertHandler(store *storage.Storage, notifier *notification.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		var alert models.Alert
		if err := c.ShouldBindJSON(&alert); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		alert.ID = uuid.New()
		alert.Status = models.StatusNew
		alert.CreatedAt = time.Now()
		alert.UpdatedAt = time.Now()

		if err := store.CreateAlert(c.Request.Context(), &alert); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		// Send notifications
		go notifier.NotifyAlert(&alert)

		c.JSON(http.StatusCreated, alert)
	}
}

func getAlertHandler(store *storage.Storage) gin.HandlerFunc {
	return func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := uuid.Parse(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid alert ID"})
			return
		}

		alert, err := store.GetAlert(c.Request.Context(), id)
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "alert not found"})
			return
		}

		c.JSON(http.StatusOK, alert)
	}
}

func updateAlertHandler(store *storage.Storage, notifier *notification.Service) gin.HandlerFunc {
	return func(c *gin.Context) {
		idStr := c.Param("id")
		id, err := uuid.Parse(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid alert ID"})
			return
		}

		var update models.AlertUpdate
		if err := c.ShouldBindJSON(&update); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		if err := store.UpdateAlert(c.Request.Context(), id, &update); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{"status": "updated"})
	}
}

func addCommentHandler(store *storage.Storage) gin.HandlerFunc {
	return func(c *gin.Context) {
		idStr := c.Param("id")
		alertID, err := uuid.Parse(idStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid alert ID"})
			return
		}

		var comment models.AlertComment
		if err := c.ShouldBindJSON(&comment); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		comment.ID = uuid.New()
		comment.AlertID = alertID
		comment.CreatedAt = time.Now()

		if err := store.AddComment(c.Request.Context(), &comment); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, comment)
	}
}

func getStatsHandler(store *storage.Storage) gin.HandlerFunc {
	return func(c *gin.Context) {
		stats, err := store.GetAlertStats(c.Request.Context())
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, stats)
	}
}
