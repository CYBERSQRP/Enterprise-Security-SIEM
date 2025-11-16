import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '../types';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          // TODO: Replace with actual API call
          const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
          });

          if (!response.ok) {
            throw new Error('Login failed');
          }

          const data = await response.json();

          set({
            user: data.user,
            tokens: {
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
              expiresAt: Date.now() + 3600 * 1000, // 1 hour
            },
            isAuthenticated: true,
          });
        } catch (error) {
          console.error('Login error:', error);
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
        });
      },

      refreshToken: async () => {
        try {
          const { tokens } = get();
          if (!tokens?.refreshToken) {
            throw new Error('No refresh token');
          }

          const response = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: tokens.refreshToken }),
          });

          if (!response.ok) {
            throw new Error('Token refresh failed');
          }

          const data = await response.json();

          set({
            tokens: {
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
              expiresAt: Date.now() + 3600 * 1000,
            },
          });
        } catch (error) {
          console.error('Token refresh error:', error);
          get().logout();
          throw error;
        }
      },

      setUser: (user: User) => set({ user }),
      setTokens: (tokens: AuthTokens) => set({ tokens }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
