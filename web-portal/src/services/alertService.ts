import { apiClient } from '../lib/api';
import type { Alert, AlertStatus } from '../types';

export interface AlertSearchParams {
  status?: AlertStatus[];
  severity?: string[];
  assignee?: string;
  rule_id?: string;
  start_time?: string;
  end_time?: string;
  limit?: number;
  offset?: number;
}

export const alertService = {
  getAlerts: async (params?: AlertSearchParams): Promise<{ alerts: Alert[]; total: number }> => {
    return apiClient.get('/api/v1/alerts', { params });
  },

  getAlert: async (id: string): Promise<Alert> => {
    return apiClient.get(`/api/v1/alerts/${id}`);
  },

  acknowledgeAlert: async (id: string): Promise<Alert> => {
    return apiClient.post(`/api/v1/alerts/${id}/acknowledge`);
  },

  assignAlert: async (id: string, assignee: string): Promise<Alert> => {
    return apiClient.post(`/api/v1/alerts/${id}/assign`, { assignee });
  },

  updateAlertStatus: async (id: string, status: AlertStatus, reason?: string): Promise<Alert> => {
    return apiClient.patch(`/api/v1/alerts/${id}`, { status, reason });
  },

  getAlertEvents: async (id: string): Promise<Event[]> => {
    return apiClient.get(`/api/v1/alerts/${id}/events`);
  },

  getAlertStats: async () => {
    return apiClient.get('/api/v1/alerts/stats');
  },
};
