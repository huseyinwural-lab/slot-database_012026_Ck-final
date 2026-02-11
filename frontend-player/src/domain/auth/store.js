import { create } from 'zustand';
import { authApi } from '@/infra/api/auth';
import { trackEvent } from '@/telemetry';
import {
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  getStoredUser,
  setStoredUser,
  clearStoredUser,
} from './session';

export const useAuthStore = create((set, get) => ({
  status: getAuthToken() ? 'authenticated' : 'idle',
  user: getStoredUser(),
  token: getAuthToken(),
  error: null,
  register: async (payload) => {
    set({ status: 'registering', error: null });
    const response = await authApi.register(payload);
    if (response.ok) {
      trackEvent('register_success', { email: payload.email });
      set({ status: 'registered', error: null });
    } else {
      set({ status: 'idle', error: response.error });
    }
    return response;
  },
  login: async (payload) => {
    set({ status: 'authenticating', error: null });
    const response = await authApi.login(payload);
    if (response.ok) {
      const token = response.data?.access_token;
      const user = response.data?.player || { email: payload.email };
      setAuthToken(token);
      setStoredUser(user);
      trackEvent('login_success', { email: payload.email });
      set({ status: 'authenticated', token, user, error: null });
    } else {
      set({ status: 'idle', error: response.error });
    }
    return response;
  },
  logout: () => {
    clearAuthToken();
    clearStoredUser();
    localStorage.removeItem('player_verification');
    set({ status: 'idle', token: null, user: null, error: null });
  },
}));
