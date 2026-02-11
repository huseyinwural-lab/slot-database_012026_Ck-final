import { create } from 'zustand';
import { verificationApi } from '@/infra/api/verification';
import { trackEvent } from '@/telemetry';

export const useVerificationStore = create((set) => ({
  emailState: 'unverified',
  smsState: 'unverified',
  error: null,
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
      set({ smsState: 'verified', error: null });
    } else {
      set({ smsState: 'failed', error: response.error });
    }
    return response;
  },
}));
