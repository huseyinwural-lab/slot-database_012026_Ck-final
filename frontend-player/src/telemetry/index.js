import { telemetryApi } from '@/infra/api/telemetry';

const QUEUE_KEY = 'player_telemetry_queue';

const loadQueue = () => {
  try {
    return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]');
  } catch {
    return [];
  }
};

const persistQueue = (queue) => {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-100)));
};

export const trackEvent = async (event, payload = {}) => {
  const record = {
    event,
    payload,
    ts: new Date().toISOString(),
  };

  try {
    await telemetryApi.sendEvent(record);
  } catch {
    const queue = loadQueue();
    queue.push(record);
    persistQueue(queue);
  }
};
