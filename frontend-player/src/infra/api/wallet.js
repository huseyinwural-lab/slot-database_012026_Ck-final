import { request } from '../http/client';

export const walletApi = {
  getBalance: () => request({ method: 'GET', url: '/player/wallet/balance' }),
  getTransactions: () => request({ method: 'GET', url: '/player/wallet/transactions' }),
  requestWithdraw: (payload) => 
    request({ 
      method: 'POST', 
      url: '/player/wallet/withdraw',
      data: payload,
      headers: { 'Idempotency-Key': crypto.randomUUID() }
    }),
};
