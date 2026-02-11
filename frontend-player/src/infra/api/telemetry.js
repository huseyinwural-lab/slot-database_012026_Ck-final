import { request } from '../http/client';

export const telemetryApi = {
  sendEvent: (payload) =>
    request({ method: 'POST', url: '/telemetry/events', data: payload }),
};
