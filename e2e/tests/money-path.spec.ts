import { test, expect, request as pwRequest } from '@playwright/test';
import crypto from 'crypto';

// --- CONFIGURATION ----------------------------------------------------------

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';

// Backend / frontend base URLs
const BACKEND_URL = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';

// LocalStorage token key used by admin UI
const LS_TOKEN_KEY = process.env.LS_TOKEN_KEY || 'admin_token';

// --- GENERIC HELPERS --------------------------------------------------------

function idemKey(prefix) {
  return `${prefix}-${Date.now()}-${crypto.randomBytes(6).toString('hex')}`;
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

const WEBHOOK_TEST_SECRET = process.env.WEBHOOK_TEST_SECRET || process.env.WEBHOOK_SECRET || 'ci_webhook_test_secret';

function webhookSigHeadersForJsonPayload(payload) {
  if (!WEBHOOK_TEST_SECRET) return {};

  const ts = Math.floor(Date.now() / 1000).toString();
  const rawBody = Buffer.from(JSON.stringify(payload));
  const sig = crypto
    .createHmac('sha256', WEBHOOK_TEST_SECRET)
    .update(`${ts}.`)
    .update(rawBody)
    .digest('hex');

  return {
    'X-Webhook-Timestamp': ts,
    'X-Webhook-Signature': sig,
  };
}

async function apiLoginAdmin(apiBaseUrl, email, password) {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });
  const res = await ctx.post('/api/v1/auth/login', {
    data: { email, password },
  });

  if (!res.ok()) {
    const body = await res.text();
    throw new Error(`admin login failed ${res.status()} body=${body}`);
  }

  const json = await res.json();
  const token = json.access_token || json.token || json.data?.access_token || json.data?.token;
  if (!token) {
    throw new Error(`admin login response missing token: ${JSON.stringify(json)}`);
  }

  return token;
}

// Player auth via real endpoints

async function apiRegisterOrLoginPlayer(apiBaseUrl, email, password) {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });

  const extractToken = (json) =>
    json?.access_token || json?.token || json?.data?.access_token || json?.data?.token || null;

  const extractPlayerId = (json) =>
    json?.player_id || json?.user?.id || json?.data?.player_id || json?.data?.user?.id || null;

  // Try login first
  let res = await ctx.post('/api/v1/auth/player/login', {
    data: { email, password, tenant_id: 'default_casino' },
  });

  let playerId = null;

  if (res.status() === 401) {
    // Register then login
    const username = email.split('@')[0];
    const reg = await ctx.post('/api/v1/auth/player/register', {
      data: {
        email,
        password,
        username,
        tenant_id: 'default_casino',
      },
    });
    if (!reg.ok()) {
      const body = await reg.text();
      throw new Error(`player register failed ${reg.status()} body=${body}`);
    }

    const regJson = await reg.json().catch(async () => ({ raw: await reg.text() }));
    playerId = extractPlayerId(regJson) || regJson?.player_id || null;

    res = await ctx.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: 'default_casino' },
    });
  }

  if (!res.ok()) {
    const body = await res.text();
    throw new Error(`player login failed ${res.status()} body=${body}`);
  }

  const json = await res.json();
  const token = extractToken(json);
  if (!token) {
    throw new Error(`player login response missing token: ${JSON.stringify(json)}`);
  }

  if (!playerId) {
    playerId = extractPlayerId(json);
  }

  if (!playerId) {
    throw new Error(`player id missing in auth responses for email=${email}`);
  }

  return { token, playerId };
}

async function adminApproveKycForPlayerId(apiBaseUrl, adminToken, playerId) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(adminToken),
  });

  const reviewRes = await ctx.post(`/api/v1/kyc/documents/${playerId}/review`, {
    data: { status: 'approved' },
  });
  const rText = await reviewRes.text();
  if (!reviewRes.ok()) {
    throw new Error(`KYC review failed ${reviewRes.status()} body=${rText}`);
  }
}

async function getBalanceNoCache(request, apiBaseUrl, playerToken) {
  const res = await request.get(`${apiBaseUrl}/api/v1/player/wallet/balance?t=${Date.now()}`, {
    headers: {
      Authorization: `Bearer ${playerToken}`,
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
    },
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}
  if (!res.ok()) {
    throw new Error(`getBalanceNoCache failed ${res.status()} body=${text}`);
  }
  return json;
}

async function pollUntil(
  fn,
  predicate,
  opts = {},
) {
  const { timeoutMs = 15000, intervalMs = 250, label = 'poll' } = opts;
  const start = Date.now();
  let last;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    last = await fn();
    if (predicate(last)) return last;
    if (Date.now() - start > timeoutMs) {
      throw new Error(`${label} timeout. last=${JSON.stringify(last)}`);
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}

function closeTo(a, b, precision = 6) {
  return Math.abs(a - b) < Math.pow(10, -precision);
}


async function playerBalance(apiBaseUrl, playerToken) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(playerToken),
  });

  const res = await ctx.get('/api/v1/player/wallet/balance');
  const json = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok()) {
    throw new Error(`balance failed ${res.status()} body=${JSON.stringify(json)}`);
  }
  return json;
}

async function playerDeposit(
  apiBaseUrl,
  playerToken,
  amount,
  mockOutcome = 'success',
) {
  const headers = {
    Authorization: `Bearer ${playerToken}`,
    'Idempotency-Key': idemKey('e2e-deposit'),
  };
  if (mockOutcome) {
    headers['X-Mock-Outcome'] = mockOutcome;
  }

  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: headers,
  });

  const res = await ctx.post('/api/v1/player/wallet/deposit', {
    data: {
      amount,
      method: 'test',
    },
  });

  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}

  if (!res.ok()) {
    throw new Error(`deposit failed ${res.status()} body=${text}`);
  }

  return { res, json };
}

async function playerWithdraw(
  apiBaseUrl,
  playerToken,
  amount,
) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: {
      Authorization: `Bearer ${playerToken}`,
      'Idempotency-Key': idemKey('e2e-withdraw'),
    },
  });

  const res = await ctx.post('/api/v1/player/wallet/withdraw', {
    data: { amount, method: 'test_bank', address: 'e2e-test-bank' },
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}

  if (!res.ok()) {
    throw new Error(`withdraw failed ${res.status()} body=${text}`);
  }

  const tx = json?.transaction || json?.data?.transaction || json;
  const txId = tx?.id || tx?.tx_id;
  if (!txId) {
    throw new Error(`withdraw response missing tx_id: ${JSON.stringify(json)}`);
  }
  return { txId };
}

async function adminApproveWithdraw(apiBaseUrl, adminToken, txId) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(adminToken),
  });
  const res = await ctx.post(`/api/v1/finance/withdrawals/${txId}/review`, {
    data: { action: 'approve' },
  });
  const text = await res.text();
  if (!res.ok()) {
    throw new Error(`approve failed ${res.status()} body=${text}`);
  }
}

async function adminListWithdrawals(apiBaseUrl, token, params) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.get('/api/v1/finance/withdrawals', { params });
  const body = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok()) throw new Error(`list withdrawals failed ${res.status()} body=${JSON.stringify(body)}`);

  return body;
}

async function adminStartPayout(
  apiBaseUrl,
  adminToken,
  txId,
  idemKey,
  outcome,
) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: {
      Authorization: `Bearer ${adminToken}`,
      'Idempotency-Key': idemKey,
      'X-Mock-Outcome': outcome,
    },
  });

  const res = await ctx.post(`/api/v1/finance/withdrawals/${txId}/payout`);
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}

  if (!res.ok()) {
    throw new Error(`payout failed ${res.status()} body=${text}`);
  }

  return json;
}

async function callPayoutWebhook(
  apiBaseUrl,
  adminToken,
  payload,
) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: {
      ...authHeaders(adminToken),
      ...webhookSigHeadersForJsonPayload(payload),
    },
  });
  const res = await ctx.post('/api/v1/finance/withdrawals/payout/webhook', {
    data: payload,
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {}
  if (!res.ok()) {
    throw new Error(`webhook failed ${res.status()} body=${text}`);
  }
  return json as any;
}

// UI helpers -----------------------------------------------------------

async function robustLogin(page: any) {
  await page.goto('/login');

  await page.getByLabel('Email').fill(OWNER_EMAIL);
  await page.getByLabel('Password').fill(OWNER_PASSWORD);

  const loginResponsePromise = page.waitForResponse((response: any) =>
    response.url().includes('/auth/login') && response.request().method() === 'POST',
  );

  await page.getByRole('button', { name: /sign in/i }).click();
  const response = await loginResponsePromise;

  if (response.status() !== 200) {
    const body = await response.text();
    throw new Error(`Login API failed with status ${response.status()} body=${body}`);
  }

  await page.waitForURL(/\/$/, { timeout: 15000 });
  await expect(page.getByText('Dashboard', { exact: true }).first()).toBeVisible({ timeout: 10000 });
}

async function setTenantContext(page: any, tenantId: string) {
  await page.evaluate((tid: string) => {
    localStorage.setItem('impersonate_tenant_id', tid);
  }, tenantId);
  await page.reload();
  await expect(page.getByText('Dashboard', { exact: true }).first()).toBeVisible({ timeout: 10000 });
}

// --- TEST SUITE: P0-6 Money Path -------------------------------------------

const PLAYER_EMAIL = process.env.E2E_PLAYER_EMAIL || 'e2e-money-path-player@example.com';
const PLAYER_PASSWORD = process.env.E2E_PLAYER_PASSWORD || 'Player123!';

const ARTIFACT_DIR = 'artifacts';

// P06-201  Admin login + withdrawals smoke

test('P06-201: Admin login + Withdrawals page smoke', async ({ page }) => {
  // Global storageState already contains admin_token + tenant context from
  // global-setup. We can directly navigate to withdrawals.
  await page.goto('/finance/withdrawals');
  await expect(page.getByRole('heading', { name: /withdrawals/i })).toBeVisible();
  await expect(page.getByText('Review, approve or reject player withdrawal requests').first()).toBeVisible();

  await page.screenshot({ path: `${ARTIFACT_DIR}/01-withdrawals-loaded.png`, fullPage: false });
});

// P06-202  Deposit success + fail net-zero

test('P06-202: Deposit success increases balance, fail is net-zero', async ({ request, page }) => {
  const adminToken = await apiLoginAdmin(BACKEND_URL, OWNER_EMAIL, OWNER_PASSWORD);
  const { token: playerToken, playerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);
  await adminApproveKycForPlayerId(BACKEND_URL, adminToken, playerId);

  const before = await playerBalance(BACKEND_URL, playerToken);

  // Success deposit
  const amount = 25;
  await playerDeposit(BACKEND_URL, playerToken, amount, 'success');
  const afterSuccess = await playerBalance(BACKEND_URL, playerToken);

  expect(afterSuccess.available_real).toBeCloseTo(before.available_real + amount, 2);
  expect(afterSuccess.held_real).toBeCloseTo(before.held_real, 2);

  // Screenshot of any admin UI context after success
  // Use existing storageState authentication instead of robustLogin
  await page.goto('/finance/withdrawals');
  await expect(page.getByRole('heading', { name: /withdrawals/i })).toBeVisible();
  await page.screenshot({ path: `${ARTIFACT_DIR}/02-deposit-success.png`, fullPage: false });

  // Fail deposit (X-Mock-Outcome=fail)
  await playerDeposit(BACKEND_URL, playerToken, amount, 'fail');
  const afterFail = await playerBalance(BACKEND_URL, playerToken);

  // Net-zero vs afterSuccess
  expect(afterFail.available_real).toBeCloseTo(afterSuccess.available_real, 2);
  expect(afterFail.held_real).toBeCloseTo(afterSuccess.held_real, 2);

  await page.screenshot({ path: `${ARTIFACT_DIR}/03-deposit-fail-net0.png`, fullPage: false });
});

// P06-203  Withdraw > approve > payout fail > retry success

test('P06-203: Withdraw -> approve -> payout fail -> retry success', async ({ page, request }) => {
  // Reuse global admin token from storageState written in global-setup.
  const fs = await import('fs');
  const path = await import('path');
  const tokenPath = path.resolve(__dirname, '../.auth/admin-token.json');
  const raw = fs.readFileSync(tokenPath, 'utf-8');
  const adminToken = JSON.parse(raw).token as string;

  // Her koşumda benzersiz player ile izolasyon
  const uniqueEmail = `e2e_p06_203_${Date.now()}@test.local`;
  const { token: playerToken, playerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, uniqueEmail, PLAYER_PASSWORD);
  await adminApproveKycForPlayerId(BACKEND_URL, adminToken, playerId);

  const withdrawAmount = 30;

  // Başlangıç: 0 balance, tek deposit + tek withdraw ile izole akış
  const before = await getBalanceNoCache(request, BACKEND_URL, playerToken);

  await playerDeposit(BACKEND_URL, playerToken, withdrawAmount + 10, 'success');
  const afterDeposit = await getBalanceNoCache(request, BACKEND_URL, playerToken);

  // 1) Withdraw requested
  const { txId } = await playerWithdraw(BACKEND_URL, playerToken, withdrawAmount);

  const afterRequested = await getBalanceNoCache(request, BACKEND_URL, playerToken);
  // Beklenen: held ≈ withdrawAmount, available ≈ afterDeposit.available - withdrawAmount
  expect(afterRequested.available_real).toBeCloseTo(afterDeposit.available_real - withdrawAmount, 6);
  expect(afterRequested.held_real).toBeCloseTo(withdrawAmount, 6);

  // 2) Approve (requested -> approved)
  await adminApproveWithdraw(BACKEND_URL, adminToken, txId);

  const listApproved = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'approved', limit: 50, offset: 0 });
  const wApproved = (listApproved.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wApproved, 'approved withdrawal must appear').toBeTruthy();

  // 3) Start payout fail
  const payoutKeyFail = idemKey('e2e-payout-fail');
  await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKeyFail, 'fail');

  const afterFailPayout = await getBalanceNoCache(request, BACKEND_URL, playerToken);
  // Held should remain same as afterRequested
  expect(afterFailPayout.available_real).toBeCloseTo(afterRequested.available_real, 6);
  expect(afterFailPayout.held_real).toBeCloseTo(afterRequested.held_real, 6);

  const listFailed = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'payout_failed', limit: 50, offset: 0 });
  const wFailed = (listFailed.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wFailed, 'payout_failed withdrawal must appear').toBeTruthy();

  await page.screenshot({ path: `${ARTIFACT_DIR}/05-payout-failed.png`, fullPage: false });

  // 4) Retry payout success
  const payoutKeySuccess = idemKey('e2e-payout-success');
  await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKeySuccess, 'success');

  // Poll until state paid ve held ≈ 0
  const finalBalance = await pollUntil(
    () => getBalanceNoCache(request, BACKEND_URL, playerToken),
    (b) => closeTo(b.held_real, 0, 6),
    { timeoutMs: 15000, intervalMs: 300, label: 'payout-success-held' },
  );

  // Held ≈ 0, available sabit kalmalı (afterFailPayout.available)
  expect(finalBalance.available_real).toBeCloseTo(afterFailPayout.available_real, 6);
  expect(finalBalance.held_real).toBeCloseTo(0, 6);

  const listPaid = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'paid', limit: 50, offset: 0 });
  const wPaid = (listPaid.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wPaid, 'paid withdrawal must appear').toBeTruthy();

  // UI badge proof is covered by P06-201 + Admin UI tests; here we focus on
  // balance + state invariants to avoid flakiness from GUI rendering.
  await page.screenshot({ path: `${ARTIFACT_DIR}/06-payout-paid.png`, fullPage: false });
});

// P06-204  Replay / Dedupe proof (payout + webhook)

test('P06-204: Replay / dedupe for payout and webhook', async ({ context, request, page }) => {
  // Reuse global admin token from storageState written in global-setup.
  const fs = await import('fs');
  const path = await import('path');
  const tokenPath = path.resolve(__dirname, '../.auth/admin-token.json');
  const raw = fs.readFileSync(tokenPath, 'utf-8');
  const adminToken = JSON.parse(raw).token as string;
  const { token: playerToken, playerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);
  await adminApproveKycForPlayerId(BACKEND_URL, adminToken, playerId);

  const withdrawAmount = 20;
  await playerDeposit(BACKEND_URL, playerToken, withdrawAmount + 5, 'success');
  const { txId } = await playerWithdraw(BACKEND_URL, playerToken, withdrawAmount);
  await adminApproveWithdraw(BACKEND_URL, adminToken, txId);

  // Payout replay idempotency
  const payoutKey = idemKey('e2e-payout-replay');
  await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKey, 'success');

  // Replay same payout multiple times  should be no-op and not throw
  for (let i = 0; i < 4; i++) {
    const json = await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKey, 'success');
    expect(json.transaction.state).toBe('paid');
  }

  // Test webhook replay with a different transaction to avoid balance conflicts
  // Create a separate transaction for webhook testing
  const uniqueEmail = `e2e_webhook_${Date.now()}@test.local`;
  const { token: webhookPlayerToken, playerId: webhookPlayerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, uniqueEmail, PLAYER_PASSWORD);
  await adminApproveKycForPlayerId(BACKEND_URL, adminToken, webhookPlayerId);
  
  await playerDeposit(BACKEND_URL, webhookPlayerToken, 15, 'success');
  const { txId: webhookTxId } = await playerWithdraw(BACKEND_URL, webhookPlayerToken, 10);
  await adminApproveWithdraw(BACKEND_URL, adminToken, webhookTxId);

  // Test webhook idempotency by calling the same webhook twice
  const providerEventId = `e2e-webhook-${Date.now()}`;
  const webhookPayload = {
    withdraw_tx_id: webhookTxId,
    provider: 'mockpsp',
    provider_event_id: providerEventId,
    status: 'paid' as const,
  };

  // First webhook call should succeed
  const firstWebhook = await callPayoutWebhook(BACKEND_URL, adminToken, webhookPayload);
  expect(firstWebhook.status).toBe('ok');

  // Second webhook call with same provider_event_id should be deduplicated
  const secondWebhook = await callPayoutWebhook(BACKEND_URL, adminToken, webhookPayload);
  expect(secondWebhook.replay).toBeTruthy();

  await context.tracing.stop({ path: `${ARTIFACT_DIR}/money-path-trace.zip` });
});
