package models

import (
	"time"

	"github.com/google/uuid"
)

type Alert struct {
	ID            uuid.UUID              `json:"id" db:"id"`
	CorrelationID *uuid.UUID             `json:"correlation_id,omitempty" db:"correlation_id"`
	Title         string                 `json:"title" db:"title"`
	Description   string                 `json:"description" db:"description"`
	Severity      Severity               `json:"severity" db:"severity"`
	Status        AlertStatus            `json:"status" db:"status"`
	SourceEvents  []string               `json:"source_events" db:"source_events"`
	AssignedTo    *string                `json:"assigned_to,omitempty" db:"assigned_to"`
	CreatedAt     time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time              `json:"updated_at" db:"updated_at"`
	ResolvedAt    *time.Time             `json:"resolved_at,omitempty" db:"resolved_at"`
	Tags          []string               `json:"tags" db:"tags"`
	Metadata      map[string]interface{} `json:"metadata" db:"metadata"`
}

type Severity string

const (
	SeverityLow      Severity = "low"
	SeverityMedium   Severity = "medium"
	SeverityHigh     Severity = "high"
	SeverityCritical Severity = "critical"
)

type AlertStatus string

const (
	StatusNew           AlertStatus = "new"
	StatusAcknowledged  AlertStatus = "acknowledged"
	StatusInProgress    AlertStatus = "in_progress"
	StatusResolved      AlertStatus = "resolved"
	StatusFalsePositive AlertStatus = "false_positive"
)

type AlertUpdate struct {
	Status     *AlertStatus `json:"status,omitempty"`
	AssignedTo *string      `json:"assigned_to,omitempty"`
	Comment    string       `json:"comment,omitempty"`
}

type AlertComment struct {
	ID        uuid.UUID `json:"id" db:"id"`
	AlertID   uuid.UUID `json:"alert_id" db:"alert_id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Comment   string    `json:"comment" db:"comment"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

type AlertFilter struct {
	Severity   []Severity    `json:"severity,omitempty"`
	Status     []AlertStatus `json:"status,omitempty"`
	AssignedTo *string       `json:"assigned_to,omitempty"`
	StartTime  *time.Time    `json:"start_time,omitempty"`
	EndTime    *time.Time    `json:"end_time,omitempty"`
	Tags       []string      `json:"tags,omitempty"`
	Limit      int           `json:"limit"`
	Offset     int           `json:"offset"`
}

type AlertStats struct {
	Total            int64                     `json:"total"`
	BySeverity       map[Severity]int64        `json:"by_severity"`
	ByStatus         map[AlertStatus]int64     `json:"by_status"`
	MeanTimeToAck    *float64                  `json:"mean_time_to_ack,omitempty"`
	MeanTimeToResolve *float64                 `json:"mean_time_to_resolve,omitempty"`
}
