import { analyticsClient } from '../lib/api';
import type { PredictiveModel, Prediction } from '../types';

export const analyticsService = {
  getModels: async (): Promise<PredictiveModel[]> => {
    return analyticsClient.get('/api/v1/models');
  },

  getModel: async (id: string): Promise<PredictiveModel> => {
    return analyticsClient.get(`/api/v1/models/${id}`);
  },

  trainModel: async (id: string, data?: any): Promise<{ status: string; accuracy: number }> => {
    return analyticsClient.post(`/api/v1/models/${id}/train`, data);
  },

  getPredictions: async (modelId: string, params?: { start_time?: string; end_time?: string }): Promise<Prediction[]> => {
    return analyticsClient.get(`/api/v1/models/${modelId}/predictions`, { params });
  },

  generateForecast: async (modelId: string, horizon: number): Promise<Prediction[]> => {
    return analyticsClient.post(`/api/v1/models/${modelId}/forecast`, { horizon });
  },

  detectAnomalies: async (data: any[]): Promise<{ anomalies: any[]; confidence: number }> => {
    return analyticsClient.post('/api/v1/analytics/anomalies', { data });
  },

  getRiskScore: async (entityId: string, entityType: 'user' | 'asset' | 'network'): Promise<{ score: number; factors: any[] }> => {
    return analyticsClient.get(`/api/v1/analytics/risk-score`, {
      params: { entity_id: entityId, entity_type: entityType }
    });
  },

  getThreatTrends: async (params?: { start_time?: string; end_time?: string }) => {
    return analyticsClient.get('/api/v1/analytics/trends', { params });
  },

  getInsights: async () => {
    return analyticsClient.get('/api/v1/analytics/insights');
  },
};
