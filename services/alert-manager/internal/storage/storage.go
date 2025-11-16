package storage

import (
	"context"

	"github.com/enterprise-siem/alert-manager/internal/models"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type Storage struct {
	postgres *PostgresStorage
	redis    *redis.Client
}

func New(databaseURL, redisURL string) (*Storage, error) {
	postgres, err := NewPostgresStorage(databaseURL)
	if err != nil {
		return nil, err
	}

	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, err
	}
	redisClient := redis.NewClient(opts)

	return &Storage{
		postgres: postgres,
		redis:    redisClient,
	}, nil
}

func (s *Storage) CreateAlert(ctx context.Context, alert *models.Alert) error {
	return s.postgres.CreateAlert(ctx, alert)
}

func (s *Storage) GetAlert(ctx context.Context, id uuid.UUID) (*models.Alert, error) {
	return s.postgres.GetAlert(ctx, id)
}

func (s *Storage) UpdateAlert(ctx context.Context, id uuid.UUID, update *models.AlertUpdate) error {
	return s.postgres.UpdateAlert(ctx, id, update)
}

func (s *Storage) ListAlerts(ctx context.Context, filter *models.AlertFilter) ([]*models.Alert, error) {
	return s.postgres.ListAlerts(ctx, filter)
}

func (s *Storage) GetAlertStats(ctx context.Context) (*models.AlertStats, error) {
	return s.postgres.GetAlertStats(ctx)
}

func (s *Storage) AddComment(ctx context.Context, comment *models.AlertComment) error {
	return s.postgres.AddComment(ctx, comment)
}

func (s *Storage) Close() error {
	s.redis.Close()
	return s.postgres.Close()
}
