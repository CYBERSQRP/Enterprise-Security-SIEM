import { threatIntelClient } from '../lib/api';
import type { ThreatFeed, IOC } from '../types';

export const threatIntelService = {
  getFeeds: async (): Promise<ThreatFeed[]> => {
    return threatIntelClient.get('/api/v1/feeds');
  },

  getFeed: async (id: string): Promise<ThreatFeed> => {
    return threatIntelClient.get(`/api/v1/feeds/${id}`);
  },

  createFeed: async (data: Partial<ThreatFeed>): Promise<ThreatFeed> => {
    return threatIntelClient.post('/api/v1/feeds', data);
  },

  updateFeed: async (id: string, data: Partial<ThreatFeed>): Promise<ThreatFeed> => {
    return threatIntelClient.patch(`/api/v1/feeds/${id}`, data);
  },

  deleteFeed: async (id: string): Promise<void> => {
    return threatIntelClient.delete(`/api/v1/feeds/${id}`);
  },

  syncFeed: async (id: string): Promise<{ status: string; ioc_count: number }> => {
    return threatIntelClient.post(`/api/v1/feeds/${id}/sync`);
  },

  searchIOCs: async (params: {
    type?: string;
    value?: string;
    severity?: string[];
    tags?: string[];
  }): Promise<IOC[]> => {
    return threatIntelClient.get('/api/v1/iocs/search', { params });
  },

  lookupIOC: async (value: string): Promise<IOC | null> => {
    return threatIntelClient.get(`/api/v1/iocs/lookup?value=${encodeURIComponent(value)}`);
  },

  addCustomIOC: async (data: Partial<IOC>): Promise<IOC> => {
    return threatIntelClient.post('/api/v1/iocs', data);
  },

  getIOCStats: async () => {
    return threatIntelClient.get('/api/v1/iocs/stats');
  },
};
