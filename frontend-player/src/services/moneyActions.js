// Player app money-path helpers: action-scoped idempotency registry + retry wrapper

const registry = new Map();

const genNonce = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
};

const buildRegistryKey = (scope, id, action) => `${scope}:${id}:${action}`;

export const getActionEntry = (scope, id, action) => {
  const key = buildRegistryKey(scope, id, action);
  return registry.get(key) || null;
};

const getOrCreateEntry = (scope, id, action) => {
  const key = buildRegistryKey(scope, id, action);
  let entry = registry.get(key);

  if (!entry || entry.status === 'done' || entry.status === 'failed') {
    entry = {
      nonce: genNonce(),
      createdAt: Date.now(),
      status: 'idle', // idle | in_flight | done | failed
    };
    registry.set(key, entry);
  }

  return { key, entry };
};

export const buildIdempotencyKey = (scope, id, action, nonce) => {
  return `${scope}:${id}:${action}:${nonce}`;
};

const isRetryableError = (error) => {
  // Network / timeout: no response object
  if (!error || !error.response) return true;

  const status = error.response.status;
  if (status === 502 || status === 503 || status === 504) return true;

  if (status >= 400 && status < 500) return false;

  return false;
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const callMoneyAction = async ({ scope, id, action, requestFn, onStatus }) => {
  const { key, entry } = getOrCreateEntry(scope, id, action);
  const idempotencyKey = buildIdempotencyKey(scope, id, action, entry.nonce);

  entry.status = 'in_flight';
  if (onStatus) onStatus('in_flight', { key, idempotencyKey });

  const attempts = [0, 250, 750];
  let lastError;

  for (let i = 0; i < attempts.length; i += 1) {
    if (i > 0 && attempts[i] > 0) {
      await sleep(attempts[i]);
    }

    try {
      const result = await requestFn(idempotencyKey);
      entry.status = 'done';
      if (onStatus) onStatus('done', { key, idempotencyKey, attempt: i });
      return result;
    } catch (err) {
      lastError = err;

      if (!isRetryableError(err)) {
        break;
      }

      if (i === attempts.length - 1) {
        break;
      }
    }
  }

  entry.status = 'failed';
  if (onStatus) onStatus('failed', { key, idempotencyKey, error: lastError });
  throw lastError;
};

export const getActionStatus = (scope, id, action) => {
  const entry = getActionEntry(scope, id, action);
  return entry ? entry.status : 'idle';
};
