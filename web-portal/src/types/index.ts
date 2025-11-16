// Common types for the SIEM platform

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'viewer';
  permissions: string[];
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AlertStatus = 'new' | 'acknowledged' | 'investigating' | 'resolved' | 'false_positive';
export type IncidentStatus = 'open' | 'investigating' | 'contained' | 'resolved' | 'closed';

export interface Event {
  id: string;
  timestamp: string;
  source: string;
  category: string;
  severity: Severity;
  message: string;
  raw_data: Record<string, any>;
  parsed_data: Record<string, any>;
  tags?: string[];
  alert_ids?: string[];
}

export interface Alert {
  id: string;
  created_at: string;
  updated_at: string;
  severity: Severity;
  status: AlertStatus;
  title: string;
  description: string;
  rule_id: string;
  rule_name: string;
  event_count: number;
  event_ids: string[];
  assignee?: string;
  tags?: string[];
  false_positive_reason?: string;
}

export interface Incident {
  id: string;
  created_at: string;
  updated_at: string;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  assignee: string;
  alert_ids: string[];
  evidence_ids: string[];
  playbook_id?: string;
  timeline: TimelineEvent[];
  tags?: string[];
}

export interface TimelineEvent {
  timestamp: string;
  type: 'alert' | 'action' | 'note' | 'evidence';
  user: string;
  description: string;
  metadata?: Record<string, any>;
}

export interface ThreatFeed {
  id: string;
  name: string;
  source: string;
  type: 'ip' | 'domain' | 'url' | 'hash' | 'email';
  enabled: boolean;
  last_updated: string;
  ioc_count: number;
  config: Record<string, any>;
}

export interface IOC {
  id: string;
  type: 'ip' | 'domain' | 'url' | 'hash' | 'email';
  value: string;
  severity: Severity;
  confidence: number;
  first_seen: string;
  last_seen: string;
  sources: string[];
  tags: string[];
  metadata?: Record<string, any>;
}

export interface Evidence {
  id: string;
  created_at: string;
  type: 'file' | 'memory' | 'network' | 'log';
  source: string;
  hash: string;
  size: number;
  chain_of_custody: ChainEntry[];
  metadata: Record<string, any>;
  analysis_results?: AnalysisResult[];
}

export interface ChainEntry {
  timestamp: string;
  user: string;
  action: string;
  signature: string;
}

export interface AnalysisResult {
  analyzer: string;
  timestamp: string;
  verdict: 'malicious' | 'suspicious' | 'clean' | 'unknown';
  confidence: number;
  details: Record<string, any>;
}

export interface CollaborationSession {
  id: string;
  incident_id: string;
  created_at: string;
  created_by: string;
  participants: Participant[];
  status: 'active' | 'ended';
}

export interface Participant {
  user_id: string;
  username: string;
  joined_at: string;
  cursor_position?: { x: number; y: number };
  color: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  user: string;
  message: string;
  timestamp: string;
}

export interface Annotation {
  id: string;
  session_id: string;
  user: string;
  type: 'highlight' | 'note' | 'tag';
  content: string;
  position: { x: number; y: number };
  timestamp: string;
}

export interface Vendor {
  id: string;
  name: string;
  domain: string;
  risk_score: number;
  last_assessment: string;
  vulnerabilities: VulnerabilityInfo[];
  compliance_status: Record<string, boolean>;
  contacts: Contact[];
}

export interface VulnerabilityInfo {
  cve_id: string;
  severity: Severity;
  description: string;
  affected_versions: string[];
  patched: boolean;
}

export interface Contact {
  name: string;
  email: string;
  role: string;
}

export interface PredictiveModel {
  id: string;
  name: string;
  type: 'threat_forecast' | 'anomaly_detection' | 'risk_prediction';
  accuracy: number;
  last_trained: string;
  predictions: Prediction[];
}

export interface Prediction {
  timestamp: string;
  type: string;
  confidence: number;
  details: Record<string, any>;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  created_by: string;
  created_at: string;
  is_default: boolean;
}

export interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'timeline' | 'map';
  title: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
}

export interface MetricData {
  name: string;
  value: number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color?: string;
  }[];
}

export interface Rule {
  id: string;
  name: string;
  description: string;
  severity: Severity;
  enabled: boolean;
  conditions: Condition[];
  actions: Action[];
  created_at: string;
  updated_at: string;
}

export interface Condition {
  field: string;
  operator: 'equals' | 'contains' | 'regex' | 'greater_than' | 'less_than';
  value: any;
}

export interface Action {
  type: 'alert' | 'email' | 'webhook' | 'script';
  config: Record<string, any>;
}
