import { create } from 'zustand';
import { walletApi } from '@/infra/api/wallet';

export const useWalletStore = create((set) => ({
  status: 'unknown',
  balance: 0,
  currency: 'USD',
  transactions: [],
  error: null,
  fetchBalance: async () => {
    set({ status: 'loading', error: null });
    const response = await walletApi.getBalance();
    if (response.ok) {
      const total = response.data?.total_real ?? response.data?.balance ?? 0;
      set({ status: 'ready', balance: total, currency: response.data?.currency || 'USD' });
    } else {
      set({ status: 'failed', error: response.error });
    }
    return response;
  },
  fetchTransactions: async () => {
    const response = await walletApi.getTransactions();
    if (response.ok) {
      set({ transactions: response.data?.transactions || [] });
    }
    return response;
  },
  markStale: () => set({ status: 'stale' }),
}));
