import { create } from 'zustand';
import { verificationApi } from '@/infra/api/verification';
import { trackEvent } from '@/telemetry';

const stored = JSON.parse(localStorage.getItem('player_verification') || '{}');

export const useVerificationStore = create((set, get) => ({
  emailState: stored.emailState || 'unverified',
  smsState: stored.smsState || 'unverified',
  error: null,
  syncFromUser: (user) => {
    if (!user) return;
    const next = {
      emailState: user.email_verified ? 'verified' : 'unverified',
      smsState: user.sms_verified ? 'verified' : 'unverified',
    };
    localStorage.setItem('player_verification', JSON.stringify(next));
    set(next);
  },
  sendEmail: async (payload) => {
    set({ emailState: 'pending', error: null });
    const response = await verificationApi.sendEmail(payload);
    if (!response.ok) {
      set({ emailState: 'failed', error: response.error });
    }
    return response;
  },
  confirmEmail: async (payload) => {
    set({ emailState: 'pending', error: null });
    const response = await verificationApi.confirmEmail(payload);
    if (response.ok) {
      trackEvent('email_verified', { email: payload.email });
      const next = { emailState: 'verified', smsState: get().smsState };
      localStorage.setItem('player_verification', JSON.stringify(next));
      set({ emailState: 'verified', error: null });
    } else {
      set({ emailState: 'failed', error: response.error });
    }
    return response;
  },
  sendSms: async (payload) => {
    set({ smsState: 'pending', error: null });
    const response = await verificationApi.sendSms(payload);
    if (!response.ok) {
      set({ smsState: 'failed', error: response.error });
    }
    return response;
  },
  confirmSms: async (payload) => {
    set({ smsState: 'pending', error: null });
    const response = await verificationApi.confirmSms(payload);
    if (response.ok) {
      trackEvent('sms_verified', { phone: payload.phone });
      const next = { emailState: get().emailState, smsState: 'verified' };
      localStorage.setItem('player_verification', JSON.stringify(next));
      set({ smsState: 'verified', error: null });
    } else {
      set({ smsState: 'failed', error: response.error });
    }
    return response;
  },
}));
