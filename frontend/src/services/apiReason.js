import api from './api';

export const postWithReason = async (url, reason, extraBody = {}) => {
  const payload = { ...extraBody, reason };
  return api.post(url, payload);
};
