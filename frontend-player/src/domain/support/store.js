import { create } from 'zustand';
import { supportApi } from '@/infra/api/support';

export const useSupportStore = create((set) => ({
  status: 'idle',
  error: null,
  openWidget: () => set({ status: 'opening', error: null }),
  widgetOpened: () => set({ status: 'opened', error: null }),
  submitTicket: async (payload) => {
    set({ status: 'sending', error: null });
    const response = await supportApi.createTicket(payload);
    if (response.ok) {
      set({ status: 'sent', error: null });
    } else {
      set({ status: 'failed', error: response.error });
    }
    return response;
  },
  reset: () => set({ status: 'idle', error: null }),
}));
