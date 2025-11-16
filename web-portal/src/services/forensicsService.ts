import { forensicsClient } from '../lib/api';
import type { Evidence, AnalysisResult } from '../types';

export const forensicsService = {
  getEvidenceList: async (params?: { type?: string; source?: string }): Promise<Evidence[]> => {
    return forensicsClient.get('/api/v1/evidence', { params });
  },

  getEvidence: async (id: string): Promise<Evidence> => {
    return forensicsClient.get(`/api/v1/evidence/${id}`);
  },

  collectEvidence: async (data: FormData): Promise<Evidence> => {
    return forensicsClient.post('/api/v1/evidence/collect', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  downloadEvidence: async (id: string): Promise<Blob> => {
    return forensicsClient.get(`/api/v1/evidence/${id}/download`, {
      responseType: 'blob',
    });
  },

  analyzeEvidence: async (id: string, analyzer: string): Promise<AnalysisResult> => {
    return forensicsClient.post(`/api/v1/evidence/${id}/analyze`, { analyzer });
  },

  verifyChainOfCustody: async (id: string): Promise<{ valid: boolean; details: any }> => {
    return forensicsClient.get(`/api/v1/evidence/${id}/verify`);
  },

  addChainEntry: async (id: string, action: string): Promise<Evidence> => {
    return forensicsClient.post(`/api/v1/evidence/${id}/chain`, { action });
  },

  getMemoryDump: async (targetId: string): Promise<{ dump_id: string }> => {
    return forensicsClient.post('/api/v1/evidence/memory-dump', { target_id: targetId });
  },

  analyzeMalware: async (fileHash: string): Promise<AnalysisResult> => {
    return forensicsClient.post('/api/v1/evidence/malware-analysis', { file_hash: fileHash });
  },
};
