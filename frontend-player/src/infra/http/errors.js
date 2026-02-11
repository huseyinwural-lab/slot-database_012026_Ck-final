import { ERROR_CODES } from './contract';

const mapStatusToCode = (status) => {
  switch (status) {
    case 401:
      return ERROR_CODES.AUTH_INVALID;
    case 403:
      return ERROR_CODES.AUTH_UNVERIFIED;
    case 422:
      return ERROR_CODES.COMPLIANCE_AGE_REQUIRED;
    default:
      return ERROR_CODES.UNKNOWN;
  }
};

export const normalizeError = (error) => {
  if (!error) {
    return { code: ERROR_CODES.UNKNOWN, message: 'Unknown error' };
  }

  const response = error.response || {};
  const payload = response.data || {};

  if (payload?.error?.code) {
    return {
      code: payload.error.code,
      message: payload.error.message || 'Request failed',
      meta: payload.error.meta || {},
    };
  }

  if (payload?.detail?.code) {
    return {
      code: payload.detail.code,
      message: payload.detail.message || payload.detail || 'Request failed',
      meta: payload.detail.meta || {},
    };
  }

  return {
    code: mapStatusToCode(response.status),
    message: payload?.detail || error.message || 'Request failed',
    meta: { status: response.status },
  };
};
