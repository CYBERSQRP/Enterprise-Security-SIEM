import { apiClient } from '../lib/api';
import { collaborationClient } from '../lib/websocket';
import type { CollaborationSession, ChatMessage, Annotation } from '../types';

export const collaborationService = {
  getSessions: async (incidentId?: string): Promise<CollaborationSession[]> => {
    return apiClient.get('/api/v1/collaboration/sessions', {
      params: { incident_id: incidentId }
    });
  },

  getSession: async (id: string): Promise<CollaborationSession> => {
    return apiClient.get(`/api/v1/collaboration/sessions/${id}`);
  },

  createSession: async (incidentId: string): Promise<CollaborationSession> => {
    return apiClient.post('/api/v1/collaboration/sessions', { incident_id: incidentId });
  },

  endSession: async (id: string): Promise<void> => {
    return apiClient.post(`/api/v1/collaboration/sessions/${id}/end`);
  },

  getChatHistory: async (sessionId: string): Promise<ChatMessage[]> => {
    return apiClient.get(`/api/v1/collaboration/sessions/${sessionId}/chat`);
  },

  getAnnotations: async (sessionId: string): Promise<Annotation[]> => {
    return apiClient.get(`/api/v1/collaboration/sessions/${sessionId}/annotations`);
  },

  // Real-time WebSocket methods
  joinSession: (sessionId: string) => {
    collaborationClient.emit('join_session', { session_id: sessionId });
  },

  leaveSession: (sessionId: string) => {
    collaborationClient.emit('leave_session', { session_id: sessionId });
  },

  sendMessage: (sessionId: string, message: string) => {
    collaborationClient.emit('message', { session_id: sessionId, message });
  },

  addAnnotation: (sessionId: string, annotation: Partial<Annotation>) => {
    collaborationClient.emit('annotation', { session_id: sessionId, annotation });
  },

  updateCursor: (sessionId: string, position: { x: number; y: number }) => {
    collaborationClient.emit('cursor', { session_id: sessionId, position });
  },

  onMessage: (callback: (message: ChatMessage) => void) => {
    collaborationClient.on('message', callback);
  },

  onAnnotation: (callback: (annotation: Annotation) => void) => {
    collaborationClient.on('annotation', callback);
  },

  onParticipantJoin: (callback: (participant: any) => void) => {
    collaborationClient.on('participant_join', callback);
  },

  onParticipantLeave: (callback: (participant: any) => void) => {
    collaborationClient.on('participant_leave', callback);
  },

  onCursorUpdate: (callback: (cursor: any) => void) => {
    collaborationClient.on('cursor_update', callback);
  },
};
