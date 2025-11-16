import { apiClient } from '../lib/api';
import type { Event } from '../types';

export interface EventSearchParams {
  query?: string;
  start_time?: string;
  end_time?: string;
  severity?: string[];
  source?: string[];
  category?: string[];
  tags?: string[];
  limit?: number;
  offset?: number;
}

export const eventService = {
  searchEvents: async (params: EventSearchParams): Promise<{ events: Event[]; total: number }> => {
    return apiClient.get('/api/v1/events/search', { params });
  },

  getEvent: async (id: string): Promise<Event> => {
    return apiClient.get(`/api/v1/events/${id}`);
  },

  getEventStats: async (params?: { start_time?: string; end_time?: string }) => {
    return apiClient.get('/api/v1/events/stats', { params });
  },

  exportEvents: async (params: EventSearchParams, format: 'json' | 'csv') => {
    return apiClient.get(`/api/v1/events/export?format=${format}`, {
      params,
      responseType: 'blob',
    });
  },
};
