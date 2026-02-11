import { request } from '../http/client';

export const authApi = {
  register: (payload) =>
    request({
      method: 'POST',
      url: '/auth/player/register',
      data: payload,
    }),
  login: (payload) =>
    request({
      method: 'POST',
      url: '/auth/player/login',
      data: payload,
    }),
};
