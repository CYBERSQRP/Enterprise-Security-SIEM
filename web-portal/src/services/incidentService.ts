import { apiClient } from '../lib/api';
import type { Incident, IncidentStatus, TimelineEvent } from '../types';

export interface CreateIncidentParams {
  title: string;
  description: string;
  severity: string;
  assignee: string;
  alert_ids?: string[];
  tags?: string[];
}

export const incidentService = {
  getIncidents: async (params?: { status?: IncidentStatus[]; assignee?: string }): Promise<Incident[]> => {
    return apiClient.get('/api/v1/incidents', { params });
  },

  getIncident: async (id: string): Promise<Incident> => {
    return apiClient.get(`/api/v1/incidents/${id}`);
  },

  createIncident: async (data: CreateIncidentParams): Promise<Incident> => {
    return apiClient.post('/api/v1/incidents', data);
  },

  updateIncident: async (id: string, data: Partial<Incident>): Promise<Incident> => {
    return apiClient.patch(`/api/v1/incidents/${id}`, data);
  },

  addTimelineEvent: async (id: string, event: Omit<TimelineEvent, 'timestamp' | 'user'>): Promise<Incident> => {
    return apiClient.post(`/api/v1/incidents/${id}/timeline`, event);
  },

  attachEvidence: async (id: string, evidenceId: string): Promise<Incident> => {
    return apiClient.post(`/api/v1/incidents/${id}/evidence`, { evidence_id: evidenceId });
  },

  executePlaybook: async (id: string, playbookId: string): Promise<{ status: string }> => {
    return apiClient.post(`/api/v1/incidents/${id}/playbook`, { playbook_id: playbookId });
  },
};
