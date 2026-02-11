import { request } from '../http/client';

export const authApi = {
  register: (payload) =>
    request({
      method: 'POST',
      url: '/api/v1/auth/player/register',
      data: payload,
    }),
  login: (payload) =>
    request({
      method: 'POST',
      url: '/api/v1/auth/player/login',
      data: payload,
    }),
};
