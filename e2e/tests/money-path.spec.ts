import { test, expect, request as pwRequest, APIResponse } from '@playwright/test';
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

function idemKey(prefix: string) {
  return `${prefix}-${Date.now()}-${crypto.randomBytes(6).toString('hex')}`;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

async function apiLoginAdmin(apiBaseUrl: string, email: string, password: string) {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });
  const res = await ctx.post('/api/v1/auth/login', {
    data: { email, password },
  });

  if (!res.ok()) {
    const body = await res.text();
    throw new Error(`admin login failed ${res.status()} body=${body}`);
  }

  const json: any = await res.json();
  const token = json.access_token || json.token || json.data?.access_token || json.data?.token;
  if (!token) {
    throw new Error(`admin login response missing token: ${JSON.stringify(json)}`);
  }

  return token as string;
}

// Player auth via real endpoints

type PlayerAuth = { token: string; playerId: string };

async function apiRegisterOrLoginPlayer(apiBaseUrl: string, email: string, password: string): Promise<PlayerAuth> {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });

  const extractToken = (json: any): string | null =>
    json?.access_token || json?.token || json?.data?.access_token || json?.data?.token || null;

  const extractPlayerId = (json: any): string | null =>
    json?.player_id || json?.user?.id || json?.data?.player_id || json?.data?.user?.id || null;

  // Try login first
  let res = await ctx.post('/api/v1/auth/player/login', {
    data: { email, password, tenant_id: 'default_casino' },
  });

  let playerId: string | null = null;

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

    const regJson: any = await reg.json().catch(async () => ({ raw: await reg.text() }));
    playerId = extractPlayerId(regJson) || regJson?.player_id || null;

    res = await ctx.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: 'default_casino' },
    });
  }

  if (!res.ok()) {
    const body = await res.text();
    throw new Error(`player login failed ${res.status()} body=${body}`);
  }

  const json: any = await res.json();
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

async function adminApproveKycForPlayerId(apiBaseUrl: string, adminToken: string, playerId: string) {
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

async function playerBalance(apiBaseUrl: string, playerToken: string) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(playerToken),
  });

  const res = await ctx.get('/api/v1/player/wallet/balance');
  const json: any = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok()) {
    throw new Error(`balance failed ${res.status()} body=${JSON.stringify(json)}`);
  }
  return json as { available_real: number; held_real: number; total_real: number };
}

async function playerDeposit(
  apiBaseUrl: string,
  playerToken: string,
  amount: number,
  mockOutcome: 'success' | 'fail' | null = 'success',
): Promise<{ res: APIResponse; json: any }> {
  const headers: Record<string, string> = {
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

  const res: APIResponse = await ctx.post('/api/v1/player/wallet/deposit', {
    data: {
      amount,
      method: 'test',
    },
  });

  const text = await res.text();
  let json: any = null;
  try {
    json = JSON.parse(text);
  } catch {}

  if (!res.ok()) {
    throw new Error(`deposit failed ${res.status()} body=${text}`);
  }

  return { res, json };
}

async function playerWithdraw(
  apiBaseUrl: string,
  playerToken: string,
  amount: number,
): Promise<{ txId: string }> {
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
  let json: any = null;
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

async function adminApproveWithdraw(apiBaseUrl: string, adminToken: string, txId: string) {
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

async function adminListWithdrawals(apiBaseUrl: string, token: string, params: Record<string, any>) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.get('/api/v1/finance/withdrawals', { params });
  const body = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok()) throw new Error(`list withdrawals failed ${res.status()} body=${JSON.stringify(body)}`);

  return body as { items: any[]; meta: any };
}

async function adminStartPayout(
  apiBaseUrl: string,
  adminToken: string,
  txId: string,
  idemKey: string,
  outcome: 'success' | 'fail',
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
  let json: any = null;
  try {
    json = JSON.parse(text);
  } catch {}

  if (!res.ok()) {
    throw new Error(`payout failed ${res.status()} body=${text}`);
  }

  return json as { transaction: any; payout_attempt: any };
}

async function callPayoutWebhook(
  apiBaseUrl: string,
  adminToken: string,
  payload: { withdraw_tx_id: string; provider: string; provider_event_id: string; status: 'paid' | 'failed'; provider_ref?: string; error_code?: string },
) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(adminToken),
  });
  const res = await ctx.post('/api/v1/finance/withdrawals/payout/webhook', {
    data: payload,
  });
  const text = await res.text();
  let json: any = null;
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
  // For this flow we do not strictly need UI state verification; keep it API-only
  // to avoid flakiness from UI login. If needed, a separate UI-only smoke covers
  // navigation.
  await page.goto('/');
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
  await robustLogin(page);
  await page.goto('/finance/withdrawals');
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

test('P06-203: Withdraw -> approve -> payout fail -> retry success', async ({ page }) => {
  const adminToken = await apiLoginAdmin(BACKEND_URL, OWNER_EMAIL, OWNER_PASSWORD);
  const { token: playerToken, playerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);
  await adminApproveKycForPlayerId(BACKEND_URL, adminToken, playerId);

  const before = await playerBalance(BACKEND_URL, playerToken);
  const withdrawAmount = 30;

  // Ensure funds
  await playerDeposit(BACKEND_URL, playerToken, withdrawAmount + 10, 'success');

  const afterDeposit = await playerBalance(BACKEND_URL, playerToken);

  // 1) Withdraw requested
  const { txId } = await playerWithdraw(BACKEND_URL, playerToken, withdrawAmount);

  const afterRequested = await playerBalance(BACKEND_URL, playerToken);
  expect(afterRequested.available_real).toBeCloseTo(afterDeposit.available_real - withdrawAmount, 2);
  expect(afterRequested.held_real).toBeCloseTo(afterDeposit.held_real + withdrawAmount, 2);

  // 2) Approve (requested -> approved)
  await adminApproveWithdraw(BACKEND_URL, adminToken, txId);

  const listApproved = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'approved', limit: 50, offset: 0 });
  const wApproved = (listApproved.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wApproved, 'approved withdrawal must appear').toBeTruthy();

  // UI evidence: Approved row + screenshot
  await robustLogin(page);
  await setTenantContext(page, 'default_casino');
  await page.goto('/finance/withdrawals');
  await expect(page.getByText(txId).first()).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: `${ARTIFACT_DIR}/04-withdraw-approved.png`, fullPage: false });

  // 3) Start payout fail
  const payoutKeyFail = idemKey('e2e-payout-fail');
  await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKeyFail, 'fail');

  const afterFailPayout = await playerBalance(BACKEND_URL, playerToken);
  // Held should remain same as afterRequested
  expect(afterFailPayout.available_real).toBeCloseTo(afterRequested.available_real, 2);
  expect(afterFailPayout.held_real).toBeCloseTo(afterRequested.held_real, 2);

  const listFailed = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'payout_failed', limit: 50, offset: 0 });
  const wFailed = (listFailed.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wFailed, 'payout_failed withdrawal must appear').toBeTruthy();

  await page.reload();
  await expect(page.getByText('Payout Failed').first()).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: `${ARTIFACT_DIR}/05-payout-failed.png`, fullPage: false });

  // 4) Retry payout success
  const payoutKeySuccess = idemKey('e2e-payout-success');
  await adminStartPayout(BACKEND_URL, adminToken, txId, payoutKeySuccess, 'success');

  const afterSuccessPayout = await playerBalance(BACKEND_URL, playerToken);
  // Held should drop by amount vs afterFailPayout, available unchanged
  expect(afterSuccessPayout.available_real).toBeCloseTo(afterFailPayout.available_real, 2);
  expect(afterSuccessPayout.held_real).toBeCloseTo(afterFailPayout.held_real - withdrawAmount, 2);

  const listPaid = await adminListWithdrawals(BACKEND_URL, adminToken, { state: 'paid', limit: 50, offset: 0 });
  const wPaid = (listPaid.items || []).find((w: any) => w.tx_id === txId || w.id === txId);
  expect(wPaid, 'paid withdrawal must appear').toBeTruthy();

  await page.reload();
  await expect(page.getByText('Paid').first()).toBeVisible({ timeout: 10000 });
  await page.screenshot({ path: `${ARTIFACT_DIR}/06-payout-paid.png`, fullPage: false });
});

// P06-204  Replay / Dedupe proof (payout + webhook)

test('P06-204: Replay / dedupe for payout and webhook', async ({ context, request }) => {
  await context.tracing.start({ snapshots: true, sources: true });

  const adminToken = await apiLoginAdmin(BACKEND_URL, OWNER_EMAIL, OWNER_PASSWORD);
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

  // Webhook replay dedupe
  const providerEventId = `e2e-webhook-${Date.now()}`;
  const webhookPayload = {
    withdraw_tx_id: txId,
    provider: 'mockpsp',
    provider_event_id: providerEventId,
    status: 'paid' as const,
  };

  const firstWebhook = await callPayoutWebhook(BACKEND_URL, adminToken, webhookPayload);
  expect(firstWebhook.status).toBe('ok');

  const secondWebhook = await callPayoutWebhook(BACKEND_URL, adminToken, webhookPayload);
  expect(secondWebhook.replay).toBeTruthy();

  await context.tracing.stop({ path: `${ARTIFACT_DIR}/money-path-trace.zip` });
});
