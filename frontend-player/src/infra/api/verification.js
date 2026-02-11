import { request } from '../http/client';

export const verificationApi = {
  sendEmail: (payload) =>
    request({
      method: 'POST',
      url: '/verify/email/send',
      data: payload,
    }),
  confirmEmail: (payload) =>
    request({
      method: 'POST',
      url: '/verify/email/confirm',
      data: payload,
    }),
  sendSms: (payload) =>
    request({
      method: 'POST',
      url: '/verify/sms/send',
      data: payload,
    }),
  confirmSms: (payload) =>
    request({
      method: 'POST',
      url: '/verify/sms/confirm',
      data: payload,
    }),
};
