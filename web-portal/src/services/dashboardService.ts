import { apiClient } from '../lib/api';
import type { Dashboard, Widget } from '../types';

export const dashboardService = {
  getDashboards: async (): Promise<Dashboard[]> => {
    return apiClient.get('/api/v1/dashboards');
  },

  getDashboard: async (id: string): Promise<Dashboard> => {
    return apiClient.get(`/api/v1/dashboards/${id}`);
  },

  createDashboard: async (data: Partial<Dashboard>): Promise<Dashboard> => {
    return apiClient.post('/api/v1/dashboards', data);
  },

  updateDashboard: async (id: string, data: Partial<Dashboard>): Promise<Dashboard> => {
    return apiClient.patch(`/api/v1/dashboards/${id}`, data);
  },

  deleteDashboard: async (id: string): Promise<void> => {
    return apiClient.delete(`/api/v1/dashboards/${id}`);
  },

  addWidget: async (dashboardId: string, widget: Partial<Widget>): Promise<Dashboard> => {
    return apiClient.post(`/api/v1/dashboards/${dashboardId}/widgets`, widget);
  },

  updateWidget: async (dashboardId: string, widgetId: string, data: Partial<Widget>): Promise<Dashboard> => {
    return apiClient.patch(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`, data);
  },

  deleteWidget: async (dashboardId: string, widgetId: string): Promise<Dashboard> => {
    return apiClient.delete(`/api/v1/dashboards/${dashboardId}/widgets/${widgetId}`);
  },
};
