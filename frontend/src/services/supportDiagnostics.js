const KEY = 'support_last_error';

export function setLastError({ requestId, message, status } = {}) {
  try {
    const payload = {
      request_id: requestId || null,
      message: message || null,
      status: status ?? null,
      ts: new Date().toISOString(),
    };
    localStorage.setItem(KEY, JSON.stringify(payload));
  } catch (e) {
    // ignore
  }
}

export function getLastError() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

export function clearLastError() {
  try {
    localStorage.removeItem(KEY);
  } catch (e) {
    // ignore
  }
}
