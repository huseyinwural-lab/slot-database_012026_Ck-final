import { request } from '../http/client';

export const walletApi = {
  getBalance: () => request({ method: 'GET', url: '/api/v1/player/wallet/balance' }),
  getTransactions: () => request({ method: 'GET', url: '/api/v1/player/wallet/transactions' }),
};
