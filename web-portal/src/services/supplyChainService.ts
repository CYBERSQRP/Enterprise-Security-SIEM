import { supplyChainClient } from '../lib/api';
import type { Vendor } from '../types';

export const supplyChainService = {
  getVendors: async (): Promise<Vendor[]> => {
    return supplyChainClient.get('/api/v1/vendors');
  },

  getVendor: async (id: string): Promise<Vendor> => {
    return supplyChainClient.get(`/api/v1/vendors/${id}`);
  },

  addVendor: async (data: Partial<Vendor>): Promise<Vendor> => {
    return supplyChainClient.post('/api/v1/vendors', data);
  },

  updateVendor: async (id: string, data: Partial<Vendor>): Promise<Vendor> => {
    return supplyChainClient.patch(`/api/v1/vendors/${id}`, data);
  },

  deleteVendor: async (id: string): Promise<void> => {
    return supplyChainClient.delete(`/api/v1/vendors/${id}`);
  },

  assessVendor: async (id: string): Promise<{ risk_score: number; report: any }> => {
    return supplyChainClient.post(`/api/v1/vendors/${id}/assess`);
  },

  getVulnerabilities: async (vendorId: string) => {
    return supplyChainClient.get(`/api/v1/vendors/${vendorId}/vulnerabilities`);
  },

  getComplianceStatus: async (vendorId: string) => {
    return supplyChainClient.get(`/api/v1/vendors/${vendorId}/compliance`);
  },

  getRiskTrends: async () => {
    return supplyChainClient.get('/api/v1/vendors/risk-trends');
  },
};
