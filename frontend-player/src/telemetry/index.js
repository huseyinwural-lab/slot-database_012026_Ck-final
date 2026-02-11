import { telemetryApi } from '@/infra/api/telemetry';
import { getStoredUser } from '@/domain/auth/storage';

const SESSION_KEY = 'player_session_id';

const getSessionId = () => {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
};

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
    session_id: getSessionId(),
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
