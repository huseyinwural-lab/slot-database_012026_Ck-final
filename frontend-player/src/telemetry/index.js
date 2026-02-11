import { telemetryApi } from '@/infra/api/telemetry';
import { getStoredUser } from '@/domain/auth/storage';

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
  const user = getStoredUser();
  const record = {
    event,
    payload,
    ts: new Date().toISOString(),
    session_id: localStorage.getItem('player_session_id'),
    player_id: user?.id || null,
    tenant_id: user?.tenant_id || null,
  };

  try {
    await telemetryApi.sendEvent(record);
  } catch {
    const queue = loadQueue();
    queue.push(record);
    persistQueue(queue);
  }
};
