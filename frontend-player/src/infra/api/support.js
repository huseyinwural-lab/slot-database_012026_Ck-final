import { request } from '../http/client';

export const supportApi = {
  createTicket: (payload) =>
    request({ method: 'POST', url: '/support/ticket', data: payload }),
};
