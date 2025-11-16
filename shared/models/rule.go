package models

import "time"

// DetectionRule represents a detection rule configuration
type DetectionRule struct {
	RuleID      string            `json:"rule_id" bson:"_id"`
	TenantID    string            `json:"tenant_id" bson:"tenant_id"`
	Version     string            `json:"version" bson:"version"`
	Metadata    RuleMetadata      `json:"metadata" bson:"metadata"`
	Type        string            `json:"type" bson:"type"`
	Category    string            `json:"category" bson:"category"`
	Severity    string            `json:"severity" bson:"severity"`
	Confidence  float64           `json:"confidence" bson:"confidence"`
	MitreAttack *MitreAttack      `json:"mitre_attack,omitempty" bson:"mitre_attack,omitempty"`
	Logic       RuleLogic         `json:"logic" bson:"logic"`
	Filters     *RuleFilters      `json:"filters,omitempty" bson:"filters,omitempty"`
	Actions     RuleActions       `json:"actions" bson:"actions"`
	Enabled     bool              `json:"enabled" bson:"enabled"`
	TestingMode bool              `json:"testing_mode" bson:"testing_mode"`
	Performance *RulePerformance  `json:"performance,omitempty" bson:"performance,omitempty"`
	CreatedAt   time.Time         `json:"created_at" bson:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at" bson:"updated_at"`
}

type RuleMetadata struct {
	Name        string    `json:"name" bson:"name"`
	Description string    `json:"description" bson:"description"`
	Author      string    `json:"author" bson:"author"`
	CreatedAt   time.Time `json:"created_at" bson:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" bson:"updated_at"`
	Tags        []string  `json:"tags,omitempty" bson:"tags,omitempty"`
}

type MitreAttack struct {
	Tactics       []string `json:"tactics,omitempty" bson:"tactics,omitempty"`
	Techniques    []string `json:"techniques,omitempty" bson:"techniques,omitempty"`
	SubTechniques []string `json:"sub_techniques,omitempty" bson:"sub_techniques,omitempty"`
}

type RuleLogic struct {
	Type       string          `json:"type" bson:"type"`
	Query      string          `json:"query" bson:"query"`
	Conditions []RuleCondition `json:"conditions,omitempty" bson:"conditions,omitempty"`
	Threshold  *Threshold      `json:"threshold,omitempty" bson:"threshold,omitempty"`
	FollowedBy *FollowedBy     `json:"followed_by,omitempty" bson:"followed_by,omitempty"`
}

type RuleCondition struct {
	Field    string      `json:"field" bson:"field"`
	Operator string      `json:"operator" bson:"operator"`
	Value    interface{} `json:"value" bson:"value"`
}

type Threshold struct {
	Count     int      `json:"count" bson:"count"`
	Timeframe string   `json:"timeframe" bson:"timeframe"`
	GroupBy   []string `json:"group_by,omitempty" bson:"group_by,omitempty"`
}

type FollowedBy struct {
	Query      string   `json:"query" bson:"query"`
	Within     string   `json:"within" bson:"within"`
	SameFields []string `json:"same_fields,omitempty" bson:"same_fields,omitempty"`
}

type RuleFilters struct {
	Whitelist *Whitelist `json:"whitelist,omitempty" bson:"whitelist,omitempty"`
}

type Whitelist struct {
	SourceIPs []string `json:"source_ips,omitempty" bson:"source_ips,omitempty"`
	Users     []string `json:"users,omitempty" bson:"users,omitempty"`
}

type RuleActions struct {
	CreateAlert    bool     `json:"create_alert" bson:"create_alert"`
	AlertSeverity  string   `json:"alert_severity,omitempty" bson:"alert_severity,omitempty"`
	Notify         []string `json:"notify,omitempty" bson:"notify,omitempty"`
	ExecutePlaybook string  `json:"execute_playbook,omitempty" bson:"execute_playbook,omitempty"`
	AutoResponse   []string `json:"auto_response,omitempty" bson:"auto_response,omitempty"`
}

type RulePerformance struct {
	AvgExecutionTimeMs int     `json:"avg_execution_time_ms" bson:"avg_execution_time_ms"`
	TriggersPerDay     int     `json:"triggers_per_day" bson:"triggers_per_day"`
	FalsePositiveRate  float64 `json:"false_positive_rate" bson:"false_positive_rate"`
}
