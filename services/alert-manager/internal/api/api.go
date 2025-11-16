package api

import (
	"net/http"

	"github.com/enterprise-siem/alert-manager/internal/notification"
	"github.com/enterprise-siem/alert-manager/internal/storage"
	"github.com/gin-gonic/gin"
)

type Server struct {
	Router   *gin.Engine
	Store    *storage.Storage
	Notifier *notification.Service
}

func SetupRoutes(router *gin.Engine, store *storage.Storage, notifier *notification.Service) {
	router.GET("/health", healthCheck)

	v1 := router.Group("/api/v1")
	{
		alerts := v1.Group("/alerts")
		{
			alerts.GET("", listAlertsHandler(store))
			alerts.POST("", createAlertHandler(store, notifier))
			alerts.GET("/:id", getAlertHandler(store))
			alerts.PATCH("/:id", updateAlertHandler(store, notifier))
			alerts.POST("/:id/comments", addCommentHandler(store))
			alerts.GET("/stats", getStatsHandler(store))
		}
	}
}

func (s *Server) Start(addr string) error {
	return s.Router.Run(addr)
}

func healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "alert-manager",
	})
}
