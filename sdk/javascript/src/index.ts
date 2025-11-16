/**
 * Enterprise SIEM JavaScript/TypeScript SDK
 *
 * Official JavaScript/TypeScript SDK for interacting with the Enterprise SIEM platform.
 *
 * @example
 * ```typescript
 * import { SIEMClient } from '@enterprise-siem/sdk';
 *
 * const client = new SIEMClient({
 *   apiUrl: 'https://siem.example.com/api',
 *   apiKey: 'your-api-key'
 * });
 *
 * // Search for events
 * const events = await client.events.search({
 *   query: 'failed_login AND user:admin',
 *   timeRange: 'last_24h'
 * });
 *
 * // Create an alert
 * const alert = await client.alerts.create({
 *   severity: 'high',
 *   title: 'Suspicious Activity Detected',
 *   description: 'Multiple failed login attempts'
 * });
 * ```
 */

export const VERSION = '1.0.0';

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface SIEMClientConfig {
  apiUrl: string;
  apiKey: string;
  timeout?: number;
  retries?: number;
}

export interface Event {
  eventId: string;
  timestamp: Date;
  eventType: string;
  severity: string;
  sourceIp?: string;
  destIp?: string;
  user?: string;
  message?: string;
  rawData?: Record<string, any>;
}

export interface Alert {
  alertId: string;
  title: string;
  severity: string;
  status: string;
  createdAt: Date;
  description?: string;
  assignedTo?: string;
}

export interface SearchEventsParams {
  query?: string;
  timeRange?: string;
  startTime?: Date;
  endTime?: Date;
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

export interface SearchEventsResponse {
  events: Event[];
  total: number;
  hasMore: boolean;
}

export interface CreateAlertParams {
  title: string;
  severity: string;
  description: string;
  eventIds?: string[];
}

export interface AIAnalysisResult {
  eventId: string;
  threatContext: {
    threatType: string;
    mitreTactics: string[];
    mitreTechniques: string[];
    riskScore: number;
  };
  recommendations: Array<{
    type: string;
    priority: number;
    description: string;
    actionItems: string[];
  }>;
  nextSteps: string[];
}

export class SIEMError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'SIEMError';
  }
}

// ============================================================================
// Events API
// ============================================================================

export class EventsAPI {
  constructor(private client: SIEMClient) {}

  /**
   * Search for security events
   */
  async search(params: SearchEventsParams = {}): Promise<SearchEventsResponse> {
    const queryParams: Record<string, string> = {
      limit: String(params.limit || 100),
      offset: String(params.offset || 0),
    };

    if (params.query) {
      queryParams.query = params.query;
    }

    if (params.timeRange) {
      queryParams.timeRange = params.timeRange;
    } else if (params.startTime && params.endTime) {
      queryParams.startTime = params.startTime.toISOString();
      queryParams.endTime = params.endTime.toISOString();
    }

    if (params.filters) {
      queryParams.filters = JSON.stringify(params.filters);
    }

    const response = await this.client.request<{
      events: any[];
      total: number;
      hasMore: boolean;
    }>('GET', '/events/search', { params: queryParams });

    return {
      events: response.events.map(this.parseEvent),
      total: response.total,
      hasMore: response.hasMore,
    };
  }

  /**
   * Get a specific event by ID
   */
  async get(eventId: string): Promise<Event> {
    const response = await this.client.request<any>('GET', `/events/${eventId}`);
    return this.parseEvent(response);
  }

  /**
   * Aggregate events by field
   */
  async aggregate(
    field: string,
    options: { query?: string; timeRange?: string } = {}
  ): Promise<Record<string, number>> {
    const params: Record<string, string> = { field };

    if (options.query) params.query = options.query;
    if (options.timeRange) params.timeRange = options.timeRange;

    const response = await this.client.request<{ aggregations: Record<string, number> }>(
      'GET',
      '/events/aggregate',
      { params }
    );

    return response.aggregations;
  }

  private parseEvent(data: any): Event {
    return {
      eventId: data.event_id,
      timestamp: new Date(data.timestamp),
      eventType: data.event_type,
      severity: data.severity,
      sourceIp: data.source_ip,
      destIp: data.dest_ip,
      user: data.user,
      message: data.message,
      rawData: data,
    };
  }
}

// ============================================================================
// Alerts API
// ============================================================================

export class AlertsAPI {
  constructor(private client: SIEMClient) {}

  /**
   * List alerts
   */
  async list(options: {
    status?: string;
    severity?: string;
    limit?: number;
  } = {}): Promise<Alert[]> {
    const params: Record<string, string> = {
      limit: String(options.limit || 100),
    };

    if (options.status) params.status = options.status;
    if (options.severity) params.severity = options.severity;

    const response = await this.client.request<{ alerts: any[] }>(
      'GET',
      '/alerts',
      { params }
    );

    return response.alerts.map(this.parseAlert);
  }

  /**
   * Create a new alert
   */
  async create(params: CreateAlertParams): Promise<Alert> {
    const response = await this.client.request<any>('POST', '/alerts', {
      body: {
        title: params.title,
        severity: params.severity,
        description: params.description,
        event_ids: params.eventIds,
      },
    });

    return this.parseAlert(response);
  }

  /**
   * Update an alert
   */
  async update(alertId: string, updates: Partial<Alert>): Promise<Alert> {
    const response = await this.client.request<any>(
      'PATCH',
      `/alerts/${alertId}`,
      { body: updates }
    );

    return this.parseAlert(response);
  }

  /**
   * Get a specific alert
   */
  async get(alertId: string): Promise<Alert> {
    const response = await this.client.request<any>('GET', `/alerts/${alertId}`);
    return this.parseAlert(response);
  }

  private parseAlert(data: any): Alert {
    return {
      alertId: data.alert_id,
      title: data.title,
      severity: data.severity,
      status: data.status,
      createdAt: new Date(data.created_at),
      description: data.description,
      assignedTo: data.assigned_to,
    };
  }
}

// ============================================================================
// Threat Intelligence API
// ============================================================================

export class ThreatIntelAPI {
  constructor(private client: SIEMClient) {}

  /**
   * Lookup an indicator of compromise
   */
  async lookupIOC(ioc: string, type: string): Promise<any> {
    return this.client.request('GET', '/threat-intel/lookup', {
      params: { ioc, type },
    });
  }

  /**
   * Add a new IOC
   */
  async addIOC(
    ioc: string,
    type: string,
    threatType: string,
    metadata: Record<string, any> = {}
  ): Promise<any> {
    return this.client.request('POST', '/threat-intel/iocs', {
      body: {
        ioc,
        type,
        threat_type: threatType,
        ...metadata,
      },
    });
  }
}

// ============================================================================
// AI API
// ============================================================================

export class AIAPI {
  constructor(private client: SIEMClient) {}

  /**
   * Analyze an alert with AI
   */
  async analyzeAlert(alertId: string): Promise<AIAnalysisResult> {
    return this.client.request<AIAnalysisResult>(
      'POST',
      `/ai/analyze/alert/${alertId}`
    );
  }

  /**
   * Run automated investigation
   */
  async investigate(eventIds: string[]): Promise<any> {
    return this.client.request('POST', '/ai/investigate', {
      body: { event_ids: eventIds },
    });
  }

  /**
   * Get AI-powered alert prioritization
   */
  async prioritizeAlerts(alertIds: string[]): Promise<any[]> {
    const response = await this.client.request<{ prioritized_alerts: any[] }>(
      'POST',
      '/ai/prioritize',
      { body: { alert_ids: alertIds } }
    );

    return response.prioritized_alerts;
  }
}

// ============================================================================
// Main Client
// ============================================================================

export class SIEMClient {
  private apiUrl: string;
  private apiKey: string;
  private timeout: number;
  private retries: number;

  public events: EventsAPI;
  public alerts: AlertsAPI;
  public threatIntel: ThreatIntelAPI;
  public ai: AIAPI;

  constructor(config: SIEMClientConfig) {
    this.apiUrl = config.apiUrl.replace(/\/$/, '');
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
    this.retries = config.retries || 3;

    // Initialize API clients
    this.events = new EventsAPI(this);
    this.alerts = new AlertsAPI(this);
    this.threatIntel = new ThreatIntelAPI(this);
    this.ai = new AIAPI(this);
  }

  /**
   * Make an API request
   */
  async request<T = any>(
    method: string,
    path: string,
    options: {
      params?: Record<string, string>;
      body?: any;
    } = {}
  ): Promise<T> {
    const url = new URL(`${this.apiUrl}${path}`);

    // Add query parameters
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const headers: Record<string, string> = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      'User-Agent': `SIEM-JS-SDK/${VERSION}`,
    };

    const fetchOptions: RequestInit = {
      method,
      headers,
    };

    if (options.body) {
      fetchOptions.body = JSON.stringify(options.body);
    }

    // Retry logic
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url.toString(), {
          ...fetchOptions,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new SIEMError(
            errorData.error || `HTTP ${response.status}`,
            response.status,
            errorData
          );
        }

        return await response.json();
      } catch (error) {
        lastError = error as Error;

        // Don't retry on client errors (4xx)
        if (error instanceof SIEMError && error.statusCode && error.statusCode < 500) {
          throw error;
        }

        // Wait before retrying (exponential backoff)
        if (attempt < this.retries - 1) {
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
        }
      }
    }

    throw lastError || new SIEMError('Request failed after retries');
  }

  /**
   * Check API health
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('GET', '/health');
  }
}

// Export everything
export default SIEMClient;
