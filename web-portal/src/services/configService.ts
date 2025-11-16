import { apiClient } from '../lib/api';
import type { Rule } from '../types';

export const configService = {
  // Rules Management
  getRules: async (): Promise<Rule[]> => {
    return apiClient.get('/api/v1/rules');
  },

  getRule: async (id: string): Promise<Rule> => {
    return apiClient.get(`/api/v1/rules/${id}`);
  },

  createRule: async (data: Partial<Rule>): Promise<Rule> => {
    return apiClient.post('/api/v1/rules', data);
  },

  updateRule: async (id: string, data: Partial<Rule>): Promise<Rule> => {
    return apiClient.patch(`/api/v1/rules/${id}`, data);
  },

  deleteRule: async (id: string): Promise<void> => {
    return apiClient.delete(`/api/v1/rules/${id}`);
  },

  testRule: async (ruleData: Partial<Rule>, testEvents: any[]): Promise<{ matches: any[] }> => {
    return apiClient.post('/api/v1/rules/test', { rule: ruleData, events: testEvents });
  },

  // Data Sources
  getDataSources: async () => {
    return apiClient.get('/api/v1/config/data-sources');
  },

  addDataSource: async (data: any) => {
    return apiClient.post('/api/v1/config/data-sources', data);
  },

  updateDataSource: async (id: string, data: any) => {
    return apiClient.patch(`/api/v1/config/data-sources/${id}`, data);
  },

  deleteDataSource: async (id: string) => {
    return apiClient.delete(`/api/v1/config/data-sources/${id}`);
  },

  // Retention Policies
  getRetentionPolicies: async () => {
    return apiClient.get('/api/v1/config/retention');
  },

  updateRetentionPolicy: async (data: any) => {
    return apiClient.put('/api/v1/config/retention', data);
  },

  // Notifications
  getNotificationSettings: async () => {
    return apiClient.get('/api/v1/config/notifications');
  },

  updateNotificationSettings: async (data: any) => {
    return apiClient.put('/api/v1/config/notifications', data);
  },

  // Users and Permissions
  getUsers: async () => {
    return apiClient.get('/api/v1/users');
  },

  createUser: async (data: any) => {
    return apiClient.post('/api/v1/users', data);
  },

  updateUser: async (id: string, data: any) => {
    return apiClient.patch(`/api/v1/users/${id}`, data);
  },

  deleteUser: async (id: string) => {
    return apiClient.delete(`/api/v1/users/${id}`);
  },

  // System Settings
  getSystemSettings: async () => {
    return apiClient.get('/api/v1/config/system');
  },

  updateSystemSettings: async (data: any) => {
    return apiClient.put('/api/v1/config/system', data);
  },
};
