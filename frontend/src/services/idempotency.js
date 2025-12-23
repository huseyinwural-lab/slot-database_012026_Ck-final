import { v4 as uuidv4 } from 'uuid';

// Helper to generate a new Idempotency-Key for money-path calls
export function makeIdempotencyKey() {
  return uuidv4();
}

// Wrap a call function and attach Idempotency-Key + in-flight lock semantics
// usage:
//   await moneyAction({
//     keyRef,
//     call: () => api.post(...),
//     onSuccess,
//   })
// keyRef is a React ref or object { current } storing last key to avoid generating multiple keys in-flight.
export async function moneyAction({ keyRef, call, onSuccess, onConflict }) {
  if (!keyRef) {
    // fallback: still single call
    return call();
  }

  if (keyRef.current?.inFlight) {
    // already in progress, ignore double click
    return;
  }

  if (!keyRef.current) {
    keyRef.current = {};
  }

  keyRef.current.inFlight = true;
  keyRef.current.key = keyRef.current.key || makeIdempotencyKey();

  try {
    const res = await call(keyRef.current.key);
    if (onSuccess) await onSuccess(res);
    return res;
  } catch (err) {
    const status = err?.response?.status;
    const code = err?.standardized?.code;

    // 409 idempotency conflict: surface a clear message
    if (status === 409 && code === 'IDEMPOTENCY_KEY_REUSE_CONFLICT' && onConflict) {
      await onConflict(err);
    }

    throw err;
  } finally {
    keyRef.current.inFlight = false;
    // keep keyRef.current.key so that retries (network/5xx) can reuse same key via caller
  }
}
