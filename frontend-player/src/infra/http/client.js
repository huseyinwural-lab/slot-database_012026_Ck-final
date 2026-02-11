import axios from 'axios';
import { env } from '@/config/env';
import { normalizeError } from './errors';

const httpClient = axios.create({
  baseURL: env.apiUrl,
  timeout: 15000,
});

httpClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('player_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const request = async (config) => {
  try {
    const response = await httpClient.request(config);
    if (response?.data?.ok !== undefined) {
      return response.data;
    }
    return { ok: true, data: response.data };
  } catch (error) {
    return { ok: false, error: normalizeError(error) };
  }
};
