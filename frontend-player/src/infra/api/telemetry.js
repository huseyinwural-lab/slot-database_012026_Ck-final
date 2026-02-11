import { request } from '../http/client';

export const telemetryApi = {
  sendEvent: (payload) =>
    request({ method: 'POST', url: '/api/v1/telemetry/events', data: payload }),
};
