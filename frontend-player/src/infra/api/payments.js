import { request } from '../http/client';

export const paymentsApi = {
  createDeposit: (payload) =>
    request({ method: 'POST', url: '/api/v1/player/wallet/deposit', data: payload }),
  getStatus: (paymentId) =>
    request({ method: 'GET', url: `/api/v1/payments/${paymentId}/status` }),
};
