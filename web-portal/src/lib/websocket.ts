import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '../store/authStore';

export type EventCallback = (data: any) => void;

class WebSocketClient {
  private socket: Socket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const { tokens } = useAuthStore.getState();

      this.socket = io(this.url, {
        auth: {
          token: tokens?.accessToken,
        },
        transports: ['websocket'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        this.reconnectAttempts++;

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          reject(new Error('Max reconnection attempts reached'));
        }
      });

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
      });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, callback: EventCallback): void {
    if (!this.socket) {
      throw new Error('Socket not connected');
    }
    this.socket.on(event, callback);
  }

  off(event: string, callback?: EventCallback): void {
    if (!this.socket) return;
    this.socket.off(event, callback);
  }

  emit(event: string, data?: any): void {
    if (!this.socket) {
      throw new Error('Socket not connected');
    }
    this.socket.emit(event, data);
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }
}

// WebSocket clients for different services
export const eventStreamClient = new WebSocketClient('ws://localhost:8083');
export const collaborationClient = new WebSocketClient('ws://localhost:8083');

// Convenience hook for event streaming
export const useEventStream = (callback: EventCallback) => {
  const connect = async () => {
    if (!eventStreamClient.isConnected()) {
      await eventStreamClient.connect();
    }
    eventStreamClient.on('event', callback);
  };

  const disconnect = () => {
    eventStreamClient.off('event', callback);
  };

  return { connect, disconnect };
};

// Convenience hook for collaboration
export const useCollaboration = (sessionId: string) => {
  const connect = async () => {
    if (!collaborationClient.isConnected()) {
      await collaborationClient.connect();
    }
    collaborationClient.emit('join_session', { session_id: sessionId });
  };

  const disconnect = () => {
    collaborationClient.emit('leave_session', { session_id: sessionId });
  };

  const sendMessage = (message: string) => {
    collaborationClient.emit('message', { session_id: sessionId, message });
  };

  const addAnnotation = (annotation: any) => {
    collaborationClient.emit('annotation', { session_id: sessionId, annotation });
  };

  const updateCursor = (position: { x: number; y: number }) => {
    collaborationClient.emit('cursor', { session_id: sessionId, position });
  };

  return { connect, disconnect, sendMessage, addAnnotation, updateCursor };
};
