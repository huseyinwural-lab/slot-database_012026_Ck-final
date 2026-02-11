import { request } from '../http/client';

export const supportApi = {
  createTicket: (payload) =>
    request({ method: 'POST', url: '/api/v1/support/ticket', data: payload }),
};
