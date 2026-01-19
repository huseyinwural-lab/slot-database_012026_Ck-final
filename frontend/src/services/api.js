import axios from 'axios';
import { setLastError } from './supportDiagnostics';

// Prefer explicit env var.
// Local dev (CRA) can override backend to avoid CORS issues when REACT_APP_BACKEND_URL
// points to an external preview domain.
const LOCAL_DEV_API_URL = process.env.REACT_APP_BACKEND_URL_LOCAL;

// Some preview environments run the app in NODE_ENV=development but are served over HTTPS
// on a non-localhost domain. In that case, using REACT_APP_BACKEND_URL_LOCAL (localhost)
// causes deterministic failures (ERR_SSL_PROTOCOL_ERROR / mixed-content).
const isLocalBrowser =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const RAW =
  process.env.NODE_ENV === 'development' && LOCAL_DEV_API_URL && isLocalBrowser
    ? LOCAL_DEV_API_URL
    : (process.env.REACT_APP_BACKEND_URL || '');

const isHttpsPage = typeof window !== 'undefined' && window.location?.protocol === 'https:';
const isHttpBackend = Boolean(RAW) && RAW.startsWith('http://');

// If the app is served over HTTPS but the configured backend is HTTP,
// do not attempt to "upgrade" to https://... (it will fail deterministically).
// Fall back to same-origin proxy instead.
const API_BASE = (isHttpsPage && isHttpBackend) ? '' : (RAW ? RAW.replace(/\/$/, '') : '');

const api = axios.create({
  baseURL: API_BASE ? (API_BASE.endsWith('/api') ? API_BASE : `${API_BASE}/api`) : '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token if available. Money-path Idempotency-Key MUST be provided
// explicitly by callers (UI helpers) – interceptor will never auto-generate it.
api.interceptors.request.use((config) => {
  try {
    const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
    const tenantId = typeof window !== 'undefined' ? localStorage.getItem('impersonate_tenant_id') : null;

    config.headers = config.headers || {};

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Owner impersonation: pass tenant context via header
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }

    // Money-path endpoints are identified here only for observability if needed,
    // but Idempotency-Key generation is handled at the call site via
    // moneyActions helpers.
    const url = config.url || '';
    const method = (config.method || 'get').toLowerCase();
    const isMoneyPath =
      method === 'post' &&
      (url.includes('/player/wallet/deposit') ||
        url.includes('/player/wallet/withdraw') ||
        url.includes('/finance/withdrawals'));

    if (isMoneyPath) {
      // Intentionally do nothing with Idempotency-Key here.
    }
  } catch (e) {
    // localStorage not available; ignore
  }
  return config;
});
// Response Interceptor for Error Standardization
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};

    // Standardize Error Object
    const raw = error.response?.data || {};
    const detail = raw.detail || {};

    const headers = error.response?.headers;
    const requestId = headers?.['x-request-id'] || headers?.['X-Request-ID'] || headers?.get?.('x-request-id') || headers?.get?.('X-Request-ID');

    const standardizedError = {
      code: raw.error_code || raw.error || detail.error_code || detail.code || 'UNKNOWN_ERROR',
      message: raw.message || detail.message || detail.detail || error.message || 'An unexpected error occurred',
      details: raw.details || detail || {},
      status: error.response?.status,
      request_id: requestId,
    };

    // Kill Switch body may be minimal and not contain details/message.
    if (standardizedError.code === 'MODULE_DISABLED') {
      standardizedError.message = 'Module disabled by Kill Switch';
      standardizedError.details = { module: raw.module };
    }

    // Persist last error for Support panel
    setLastError({
      requestId: standardizedError.request_id,
      message: standardizedError.message,
      status: standardizedError.status,
    });
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('support:last_error'));
    }

    const hasShownToast = Boolean(originalRequest.__reqid_toast_shown);

    const formatRequestId = () => `Request ID: ${standardizedError.request_id || 'unavailable'}`;

    const copyRequestId = async () => {
      try {
        if (!standardizedError.request_id) return;
        await navigator.clipboard.writeText(standardizedError.request_id);
         
        const { toast } = await import('sonner');
        toast.success('Copied request id');
      } catch (e) {
        // ignore
      }
    };

    const showToast = async (type, title, description) => {
      if (hasShownToast) return;
       
      originalRequest.__reqid_toast_shown = true;

       
      const { toast } = await import('sonner');

      const hasCopy = Boolean(standardizedError.request_id);
      const action = hasCopy
        ? {
            label: 'Copy',
            onClick: copyRequestId,
          }
        : undefined;

      const desc = `${description}\n${formatRequestId()}`;

      if (type === 'error') toast.error(title, { description: desc, action });
      else if (type === 'warning') toast.warning(title, { description: desc, action });
      else toast.message(title, { description: desc, action });
    };

    // 401: Unauthorized -> Logout + toast
    if (error.response?.status === 401) {
      await showToast('warning', 'Unauthorized', 'Session invalid. Please sign in again.');
      if (typeof window !== 'undefined') {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('admin_user');
        if (!window.location.pathname.includes('/login')) {
          // Allow toast to render before redirect
          await new Promise((r) => setTimeout(r, 1200));
          window.location.href = '/login';
        }
      }
    }

    // 429: Too many requests
    if (error.response?.status === 429) {
      showToast('warning', 'Too many requests', 'Please wait and try again.');
    }

    // Network error (no response)
    if (!error.response) {
      showToast('error', 'Network error', 'Backend is unreachable.');
    }

    // 5xx server errors
    if (error.response?.status >= 500) {
      showToast('error', 'Server error', 'Something went wrong on the server.');
    }

    // 403: Forbidden -> keep console warn (no redirect)
    if (error.response?.status === 403) {
      console.warn('Access Forbidden:', standardizedError.message);
    }

    // Attach standardized error to the rejection
    error.standardized = standardizedError;
    return Promise.reject(error);
  }
);

export default api;
