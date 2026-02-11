import { create } from 'zustand';
import { supportApi } from '@/infra/api/support';
import { getStoredUser } from '@/domain/auth/session';

export const useSupportStore = create((set) => ({
  status: 'idle',
  error: null,
  openWidget: () => set({ status: 'opening', error: null }),
  widgetOpened: () => set({ status: 'opened', error: null }),
  submitTicket: async (payload) => {
    set({ status: 'sending', error: null });
    const user = getStoredUser();
    const enriched = {
      ...payload,
      player_id: user?.id,
      tenant_id: user?.tenant_id || 'default_casino',
    };
    const response = await supportApi.createTicket(enriched);
    if (response.ok) {
      set({ status: 'sent', error: null });
    } else {
      set({ status: 'failed', error: response.error });
    }
    return response;
  },
  reset: () => set({ status: 'idle', error: null }),
}));
