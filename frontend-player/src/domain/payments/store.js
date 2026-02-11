import { create } from 'zustand';
import { paymentsApi } from '@/infra/api/payments';
import { trackEvent } from '@/telemetry';

export const usePaymentsStore = create((set) => ({
  status: 'idle',
  lastPaymentId: null,
  redirectUrl: null,
  error: null,
  createDeposit: async (payload) => {
    set({ status: 'initializing', error: null });
    const response = await paymentsApi.createDeposit({
      ...payload,
      method: payload.method || 'stripe',
    });
    if (response.ok) {
      set({
        status: 'pending',
        lastPaymentId: response.data?.transaction_id || null,
        redirectUrl: response.data?.redirect_url || null,
      });
      trackEvent('payment_pending', { payment_id: response.data?.transaction_id });
    } else {
      set({ status: 'failed', error: response.error });
    }
    return response;
  },
  reset: () => set({ status: 'idle', lastPaymentId: null, redirectUrl: null, error: null }),
}));
