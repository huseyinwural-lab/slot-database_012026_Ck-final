import { request } from '../http/client';

export const paymentsApi = {
  createDeposit: (payload) =>
    request({
      method: 'POST',
      url: '/player/wallet/deposit',
      data: payload,
      headers: {
        'Idempotency-Key': crypto.randomUUID(),
      },
    }),
  getStatus: (paymentId) =>
    request({ method: 'GET', url: `/payments/${paymentId}/status` }),
};
