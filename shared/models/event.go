package models

import "time"

// CommonEvent represents the normalized event format
type CommonEvent struct {
	EventID        string         `json:"event_id" bson:"event_id"`
	EventVersion   string         `json:"event_version" bson:"event_version"`
	Timestamp      time.Time      `json:"timestamp" bson:"timestamp"`
	IngestionTime  time.Time      `json:"ingestion_time" bson:"ingestion_time"`
	TenantID       string         `json:"tenant_id" bson:"tenant_id"`
	Source         Source         `json:"source" bson:"source"`
	Event          Event          `json:"event" bson:"event"`
	User           *User          `json:"user,omitempty" bson:"user,omitempty"`
	Destination    *Destination   `json:"destination,omitempty" bson:"destination,omitempty"`
	Network        *Network       `json:"network,omitempty" bson:"network,omitempty"`
	File           *File          `json:"file,omitempty" bson:"file,omitempty"`
	Process        *Process       `json:"process,omitempty" bson:"process,omitempty"`
	Threat         *Threat        `json:"threat,omitempty" bson:"threat,omitempty"`
	Enrichment     *Enrichment    `json:"enrichment,omitempty" bson:"enrichment,omitempty"`
	Metadata       Metadata       `json:"metadata" bson:"metadata"`
	Raw            Raw            `json:"raw" bson:"raw"`
}

type Source struct {
	Type     string    `json:"type" bson:"type"`
	Category string    `json:"category" bson:"category"`
	Product  string    `json:"product" bson:"product"`
	Vendor   string    `json:"vendor" bson:"vendor"`
	Hostname string    `json:"hostname" bson:"hostname"`
	IP       string    `json:"ip" bson:"ip"`
	MAC      string    `json:"mac,omitempty" bson:"mac,omitempty"`
	FQDN     string    `json:"fqdn,omitempty" bson:"fqdn,omitempty"`
	Zone     string    `json:"zone,omitempty" bson:"zone,omitempty"`
	Location *Location `json:"location,omitempty" bson:"location,omitempty"`
}

type Location struct {
	Datacenter string       `json:"datacenter,omitempty" bson:"datacenter,omitempty"`
	Rack       string       `json:"rack,omitempty" bson:"rack,omitempty"`
	Geo        *GeoLocation `json:"geo,omitempty" bson:"geo,omitempty"`
}

type GeoLocation struct {
	Country string  `json:"country" bson:"country"`
	City    string  `json:"city" bson:"city"`
	Lat     float64 `json:"lat" bson:"lat"`
	Lon     float64 `json:"lon" bson:"lon"`
}

type Event struct {
	Type        string  `json:"type" bson:"type"`
	Action      string  `json:"action" bson:"action"`
	Outcome     string  `json:"outcome" bson:"outcome"`
	Severity    string  `json:"severity" bson:"severity"`
	Category    string  `json:"category" bson:"category"`
	Name        string  `json:"name" bson:"name"`
	Description string  `json:"description,omitempty" bson:"description,omitempty"`
	RiskScore   int     `json:"risk_score,omitempty" bson:"risk_score,omitempty"`
	Confidence  float64 `json:"confidence,omitempty" bson:"confidence,omitempty"`
}

type User struct {
	ID         string   `json:"id,omitempty" bson:"id,omitempty"`
	Username   string   `json:"username" bson:"username"`
	Email      string   `json:"email,omitempty" bson:"email,omitempty"`
	Domain     string   `json:"domain,omitempty" bson:"domain,omitempty"`
	FullName   string   `json:"full_name,omitempty" bson:"full_name,omitempty"`
	Department string   `json:"department,omitempty" bson:"department,omitempty"`
	Title      string   `json:"title,omitempty" bson:"title,omitempty"`
	Manager    string   `json:"manager,omitempty" bson:"manager,omitempty"`
	Roles      []string `json:"roles,omitempty" bson:"roles,omitempty"`
	Groups     []string `json:"groups,omitempty" bson:"groups,omitempty"`
	RiskScore  int      `json:"risk_score,omitempty" bson:"risk_score,omitempty"`
}

type Destination struct {
	IP       string `json:"ip" bson:"ip"`
	Port     int    `json:"port,omitempty" bson:"port,omitempty"`
	Hostname string `json:"hostname,omitempty" bson:"hostname,omitempty"`
	FQDN     string `json:"fqdn,omitempty" bson:"fqdn,omitempty"`
	Service  string `json:"service,omitempty" bson:"service,omitempty"`
	Zone     string `json:"zone,omitempty" bson:"zone,omitempty"`
}

type Network struct {
	Protocol        string `json:"protocol,omitempty" bson:"protocol,omitempty"`
	Direction       string `json:"direction,omitempty" bson:"direction,omitempty"`
	BytesSent       int64  `json:"bytes_sent,omitempty" bson:"bytes_sent,omitempty"`
	BytesReceived   int64  `json:"bytes_received,omitempty" bson:"bytes_received,omitempty"`
	PacketsSent     int    `json:"packets_sent,omitempty" bson:"packets_sent,omitempty"`
	PacketsReceived int    `json:"packets_received,omitempty" bson:"packets_received,omitempty"`
	SessionID       string `json:"session_id,omitempty" bson:"session_id,omitempty"`
	VLANID          int    `json:"vlan_id,omitempty" bson:"vlan_id,omitempty"`
	Application     string `json:"application,omitempty" bson:"application,omitempty"`
}

type File struct {
	Path        string     `json:"path" bson:"path"`
	Name        string     `json:"name" bson:"name"`
	Extension   string     `json:"extension,omitempty" bson:"extension,omitempty"`
	Size        int64      `json:"size,omitempty" bson:"size,omitempty"`
	Hash        *FileHash  `json:"hash,omitempty" bson:"hash,omitempty"`
	Owner       string     `json:"owner,omitempty" bson:"owner,omitempty"`
	Permissions string     `json:"permissions,omitempty" bson:"permissions,omitempty"`
	Created     *time.Time `json:"created,omitempty" bson:"created,omitempty"`
	Modified    *time.Time `json:"modified,omitempty" bson:"modified,omitempty"`
	Accessed    *time.Time `json:"accessed,omitempty" bson:"accessed,omitempty"`
}

type FileHash struct {
	MD5    string `json:"md5,omitempty" bson:"md5,omitempty"`
	SHA1   string `json:"sha1,omitempty" bson:"sha1,omitempty"`
	SHA256 string `json:"sha256,omitempty" bson:"sha256,omitempty"`
}

type Process struct {
	PID             int          `json:"pid" bson:"pid"`
	Name            string       `json:"name" bson:"name"`
	Path            string       `json:"path,omitempty" bson:"path,omitempty"`
	CommandLine     string       `json:"command_line,omitempty" bson:"command_line,omitempty"`
	User            string       `json:"user,omitempty" bson:"user,omitempty"`
	ParentPID       int          `json:"parent_pid,omitempty" bson:"parent_pid,omitempty"`
	ParentName      string       `json:"parent_name,omitempty" bson:"parent_name,omitempty"`
	Hash            *ProcessHash `json:"hash,omitempty" bson:"hash,omitempty"`
	SignatureStatus string       `json:"signature_status,omitempty" bson:"signature_status,omitempty"`
}

type ProcessHash struct {
	SHA256 string `json:"sha256" bson:"sha256"`
}

type Threat struct {
	Framework      string    `json:"framework,omitempty" bson:"framework,omitempty"`
	Tactic         []string  `json:"tactic,omitempty" bson:"tactic,omitempty"`
	Technique      []string  `json:"technique,omitempty" bson:"technique,omitempty"`
	IndicatorType  string    `json:"indicator_type,omitempty" bson:"indicator_type,omitempty"`
	IndicatorValue string    `json:"indicator_value,omitempty" bson:"indicator_value,omitempty"`
	MalwareFamily  string    `json:"malware_family,omitempty" bson:"malware_family,omitempty"`
	ThreatActor    string    `json:"threat_actor,omitempty" bson:"threat_actor,omitempty"`
	Confidence     float64   `json:"confidence,omitempty" bson:"confidence,omitempty"`
	Severity       string    `json:"severity,omitempty" bson:"severity,omitempty"`
	FirstSeen      time.Time `json:"first_seen,omitempty" bson:"first_seen,omitempty"`
	LastSeen       time.Time `json:"last_seen,omitempty" bson:"last_seen,omitempty"`
	Source         string    `json:"source,omitempty" bson:"source,omitempty"`
}

type Enrichment struct {
	GeoIP       *GeoIPEnrichment       `json:"geo_ip,omitempty" bson:"geo_ip,omitempty"`
	Asset       *AssetEnrichment       `json:"asset,omitempty" bson:"asset,omitempty"`
	UserContext *UserContextEnrichment `json:"user_context,omitempty" bson:"user_context,omitempty"`
}

type GeoIPEnrichment struct {
	Country   string `json:"country,omitempty" bson:"country,omitempty"`
	City      string `json:"city,omitempty" bson:"city,omitempty"`
	ASN       string `json:"asn,omitempty" bson:"asn,omitempty"`
	Org       string `json:"org,omitempty" bson:"org,omitempty"`
	IsVPN     bool   `json:"is_vpn" bson:"is_vpn"`
	IsProxy   bool   `json:"is_proxy" bson:"is_proxy"`
	IsTor     bool   `json:"is_tor" bson:"is_tor"`
	IsHosting bool   `json:"is_hosting" bson:"is_hosting"`
}

type AssetEnrichment struct {
	Criticality     string   `json:"criticality,omitempty" bson:"criticality,omitempty"`
	Owner           string   `json:"owner,omitempty" bson:"owner,omitempty"`
	CostCenter      string   `json:"cost_center,omitempty" bson:"cost_center,omitempty"`
	ComplianceScope []string `json:"compliance_scope,omitempty" bson:"compliance_scope,omitempty"`
	Tags            []string `json:"tags,omitempty" bson:"tags,omitempty"`
}

type UserContextEnrichment struct {
	NormalLoginHours    string   `json:"normal_login_hours,omitempty" bson:"normal_login_hours,omitempty"`
	NormalLocations     []string `json:"normal_locations,omitempty" bson:"normal_locations,omitempty"`
	NormalDevices       []string `json:"normal_devices,omitempty" bson:"normal_devices,omitempty"`
	AvgLoginFrequency   int      `json:"avg_login_frequency,omitempty" bson:"avg_login_frequency,omitempty"`
	LastPasswordChange  *time.Time `json:"last_password_change,omitempty" bson:"last_password_change,omitempty"`
}

type Metadata struct {
	CorrelationID   string   `json:"correlation_id,omitempty" bson:"correlation_id,omitempty"`
	ParentEventID   string   `json:"parent_event_id,omitempty" bson:"parent_event_id,omitempty"`
	RelatedEvents   []string `json:"related_events,omitempty" bson:"related_events,omitempty"`
	Tags            []string `json:"tags,omitempty" bson:"tags,omitempty"`
	Notes           string   `json:"notes,omitempty" bson:"notes,omitempty"`
	PipelineVersion string   `json:"pipeline_version,omitempty" bson:"pipeline_version,omitempty"`
	RetentionDays   int      `json:"retention_days" bson:"retention_days"`
}

type Raw struct {
	Message string `json:"message" bson:"message"`
	Format  string `json:"format" bson:"format"`
}
