import { request } from '../http/client';

export const walletApi = {
  getBalance: () => request({ method: 'GET', url: '/player/wallet/balance' }),
  getTransactions: () => request({ method: 'GET', url: '/player/wallet/transactions' }),
};
