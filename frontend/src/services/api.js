import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL.endsWith('/api') ? API_URL : `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token if available
api.interceptors.request.use((config) => {
  try {
    const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
    if (token) {
      // eslint-disable-next-line no-param-reassign
      config.headers = config.headers || {};
      // eslint-disable-next-line no-param-reassign
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (e) {
    // localStorage not available; ignore
  }
  return config;
});

export default api;
