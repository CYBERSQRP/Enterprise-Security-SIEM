package storage

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/enterprise-siem/alert-manager/internal/models"
	"github.com/google/uuid"
	"github.com/lib/pq"
	_ "github.com/lib/pq"
)

type PostgresStorage struct {
	db *sql.DB
}

func NewPostgresStorage(databaseURL string) (*PostgresStorage, error) {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &PostgresStorage{db: db}, nil
}

func (s *PostgresStorage) CreateAlert(ctx context.Context, alert *models.Alert) error {
	metadataJSON, err := json.Marshal(alert.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	query := `
		INSERT INTO alerts (id, correlation_id, title, description, severity, status,
			source_events, assigned_to, created_at, updated_at, tags, metadata)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
	`

	_, err = s.db.ExecContext(ctx, query,
		alert.ID,
		alert.CorrelationID,
		alert.Title,
		alert.Description,
		alert.Severity,
		alert.Status,
		pq.Array(alert.SourceEvents),
		alert.AssignedTo,
		alert.CreatedAt,
		alert.UpdatedAt,
		pq.Array(alert.Tags),
		metadataJSON,
	)

	return err
}

func (s *PostgresStorage) GetAlert(ctx context.Context, id uuid.UUID) (*models.Alert, error) {
	query := `
		SELECT id, correlation_id, title, description, severity, status,
			source_events, assigned_to, created_at, updated_at, resolved_at, tags, metadata
		FROM alerts
		WHERE id = $1
	`

	alert := &models.Alert{}
	var metadataJSON []byte
	var sourceEvents, tags pq.StringArray

	err := s.db.QueryRowContext(ctx, query, id).Scan(
		&alert.ID,
		&alert.CorrelationID,
		&alert.Title,
		&alert.Description,
		&alert.Severity,
		&alert.Status,
		&sourceEvents,
		&alert.AssignedTo,
		&alert.CreatedAt,
		&alert.UpdatedAt,
		&alert.ResolvedAt,
		&tags,
		&metadataJSON,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("alert not found")
	}
	if err != nil {
		return nil, err
	}

	alert.SourceEvents = sourceEvents
	alert.Tags = tags

	if err := json.Unmarshal(metadataJSON, &alert.Metadata); err != nil {
		return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
	}

	return alert, nil
}

func (s *PostgresStorage) UpdateAlert(ctx context.Context, id uuid.UUID, update *models.AlertUpdate) error {
	query := `
		UPDATE alerts
		SET status = COALESCE($2, status),
			assigned_to = COALESCE($3, assigned_to),
			updated_at = $4,
			resolved_at = CASE WHEN $2 = 'resolved' THEN $4 ELSE resolved_at END
		WHERE id = $1
	`

	now := time.Now()
	_, err := s.db.ExecContext(ctx, query, id, update.Status, update.AssignedTo, now)
	return err
}

func (s *PostgresStorage) ListAlerts(ctx context.Context, filter *models.AlertFilter) ([]*models.Alert, error) {
	query := `
		SELECT id, correlation_id, title, description, severity, status,
			source_events, assigned_to, created_at, updated_at, resolved_at, tags, metadata
		FROM alerts
		WHERE 1=1
	`

	args := []interface{}{}
	argPos := 1

	if len(filter.Severity) > 0 {
		query += fmt.Sprintf(" AND severity = ANY($%d)", argPos)
		args = append(args, pq.Array(filter.Severity))
		argPos++
	}

	if len(filter.Status) > 0 {
		query += fmt.Sprintf(" AND status = ANY($%d)", argPos)
		args = append(args, pq.Array(filter.Status))
		argPos++
	}

	if filter.StartTime != nil {
		query += fmt.Sprintf(" AND created_at >= $%d", argPos)
		args = append(args, filter.StartTime)
		argPos++
	}

	if filter.EndTime != nil {
		query += fmt.Sprintf(" AND created_at <= $%d", argPos)
		args = append(args, filter.EndTime)
		argPos++
	}

	query += " ORDER BY created_at DESC"
	query += fmt.Sprintf(" LIMIT $%d OFFSET $%d", argPos, argPos+1)
	args = append(args, filter.Limit, filter.Offset)

	rows, err := s.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	alerts := []*models.Alert{}
	for rows.Next() {
		alert := &models.Alert{}
		var metadataJSON []byte
		var sourceEvents, tags pq.StringArray

		err := rows.Scan(
			&alert.ID,
			&alert.CorrelationID,
			&alert.Title,
			&alert.Description,
			&alert.Severity,
			&alert.Status,
			&sourceEvents,
			&alert.AssignedTo,
			&alert.CreatedAt,
			&alert.UpdatedAt,
			&alert.ResolvedAt,
			&tags,
			&metadataJSON,
		)
		if err != nil {
			return nil, err
		}

		alert.SourceEvents = sourceEvents
		alert.Tags = tags
		if err := json.Unmarshal(metadataJSON, &alert.Metadata); err != nil {
			return nil, err
		}

		alerts = append(alerts, alert)
	}

	return alerts, nil
}

func (s *PostgresStorage) GetAlertStats(ctx context.Context) (*models.AlertStats, error) {
	stats := &models.AlertStats{
		BySeverity: make(map[models.Severity]int64),
		ByStatus:   make(map[models.AlertStatus]int64),
	}

	// Get total count
	err := s.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM alerts").Scan(&stats.Total)
	if err != nil {
		return nil, err
	}

	// Get counts by severity
	rows, err := s.db.QueryContext(ctx, "SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var severity models.Severity
		var count int64
		if err := rows.Scan(&severity, &count); err != nil {
			return nil, err
		}
		stats.BySeverity[severity] = count
	}

	// Get counts by status
	rows, err = s.db.QueryContext(ctx, "SELECT status, COUNT(*) FROM alerts GROUP BY status")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var status models.AlertStatus
		var count int64
		if err := rows.Scan(&status, &count); err != nil {
			return nil, err
		}
		stats.ByStatus[status] = count
	}

	return stats, nil
}

func (s *PostgresStorage) AddComment(ctx context.Context, comment *models.AlertComment) error {
	query := `
		INSERT INTO alert_comments (id, alert_id, user_id, comment, created_at)
		VALUES ($1, $2, $3, $4, $5)
	`

	_, err := s.db.ExecContext(ctx, query,
		comment.ID,
		comment.AlertID,
		comment.UserID,
		comment.Comment,
		comment.CreatedAt,
	)

	return err
}

func (s *PostgresStorage) Close() error {
	return s.db.Close()
}
