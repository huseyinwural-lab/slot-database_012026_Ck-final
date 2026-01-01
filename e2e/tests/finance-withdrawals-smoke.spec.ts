import { test, expect, request as pwRequest, APIResponse } from '@playwright/test';
import crypto from 'crypto';

// LocalStorage token key used by admin UI
const LS_TOKEN_KEY = process.env.LS_TOKEN_KEY || 'admin_token';

// Backend / frontend base URLs
const BACKEND_URL = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001'; // FastAPI root (behind /api)
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';

// Admin (owner) creds - must match environment or be overridden by env
const OWNER_EMAIL = process.env.OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.OWNER_PASSWORD || 'Admin123!';

// Player creds - we will register on-the-fly if needed
const PLAYER_EMAIL = process.env.PLAYER_EMAIL || 'e2e-player@example.com';
const PLAYER_PASSWORD = process.env.PLAYER_PASSWORD || 'Player123!';

// Player withdraw endpoint (already exists)
const PLAYER_WITHDRAW_REQUEST_PATH =
  process.env.PLAYER_WITHDRAW_REQUEST_PATH || '/api/v1/player/wallet/withdraw';

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

function idemKey(prefix: string) {
  return `${prefix}-${Date.now()}-${crypto.randomBytes(6).toString('hex')}`;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

async function playerDeposit(apiBaseUrl: string, playerToken: string, amount: number) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: {
      Authorization: `Bearer ${playerToken}`,
      'Idempotency-Key': idemKey('e2e-deposit'),
    },
  });

  const res: APIResponse = await ctx.post('/api/v1/player/wallet/deposit', {
    data: {
      amount,
      method: 'test',
    },
  });

  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch {}

  if (!res.ok()) {
    throw new Error(`deposit failed ${res.status()} body=${text}`);
  }

  return { res, json, text };
}

async function adminListWithdrawals(apiBaseUrl: string, token: string, params: Record<string, any>) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.get('/api/v1/finance/withdrawals', { params });
  const body = await res.json().catch(async () => ({ raw: await res.text() }));
  if (!res.ok()) throw new Error(`list withdrawals failed ${res.status()} body=${JSON.stringify(body)}`);

  return body;
}

async function adminApprove(apiBaseUrl: string, token: string, txId: string) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.post(`/api/v1/finance/withdrawals/${txId}/review`, {
    data: { action: 'approve' },
  });
  return res;
}

async function adminMarkPaid(apiBaseUrl: string, token: string, txId: string) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.post(`/api/v1/finance/withdrawals/${txId}/mark-paid`);
  return res;
}

async function adminApproveKycForPlayerId(apiBaseUrl: string, adminToken: string, playerId: string) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(adminToken),
  });

  // In the mock KYC implementation, review_document treats doc_id as player_id when it
  // cannot extract a document mapping. We can therefore call it directly with playerId
  // to set kyc_status = 'verified' deterministically without relying on queue ordering.
  const reviewRes = await ctx.post(`/api/v1/kyc/documents/${playerId}/review`, {
    data: { status: 'approved' },
  });

  const rText = await reviewRes.text();
  if (!reviewRes.ok()) {
    throw new Error(`KYC review failed ${reviewRes.status()} body=${rText}`);
  }

  return { docId: playerId };
}

async function playerRequestWithdraw(apiBaseUrl: string, token: string, payload: any) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: authHeaders(token),
  });

  const res = await ctx.post(PLAYER_WITHDRAW_REQUEST_PATH, { data: payload, headers: {
    'Idempotency-Key': `e2e-withdraw-${Date.now()}-${Math.random()}`,
  }} as any);

  const text = await res.text();
  let json: any = null;
  try { json = JSON.parse(text); } catch {}
  return { res, json, text };
}

// --- Smoke Test ---

test.describe('Finance Withdrawals Smoke', () => {
  test('player withdraw -> admin approve -> admin mark-paid (state + invariants)', async ({ page }) => {
    // 1) Token’ları API ile al
    const ownerToken = await apiLoginAdmin(BACKEND_URL, OWNER_EMAIL, OWNER_PASSWORD);
    const { token: playerToken, playerId } = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);

    // Ensure KYC is verified via admin KYC queue using player_id
    await adminApproveKycForPlayerId(BACKEND_URL, ownerToken, playerId);

    // 2) Admin token’ı UI localStorage’a enjekte et (UI login yok)
    await page.addInitScript(
      ({ key, token }) => {
        window.localStorage.setItem(key, token);
      },
      { key: LS_TOKEN_KEY, token: ownerToken }
    );

    await page.goto(`${FRONTEND_URL}/finance/withdrawals`, { waitUntil: 'domcontentloaded' });

    // UI route açıldı mı? (gate)
    await expect(page.getByRole('heading', { name: /withdrawals/i })).toBeVisible();

    // 3) Player funding (deposit) before withdraw to avoid INSUFFICIENT_FUNDS
    const withdrawAmount = Number(process.env.WITHDRAW_AMOUNT || '10');
    const depositBuffer = Number(process.env.DEPOSIT_BUFFER || '5');
    const depositAmount = withdrawAmount + depositBuffer;

    await playerDeposit(BACKEND_URL, playerToken, depositAmount);

    // 4) Player withdraw request oluştur (API)
    const amount = withdrawAmount;

    const { res: reqRes, json: reqJson, text: reqText } = await playerRequestWithdraw(
      BACKEND_URL,
      playerToken,
      { amount, method: 'test_bank', address: 'e2e-test-bank' },
    );

    if (!reqRes.ok()) {
      throw new Error(
        `player withdraw request failed ${reqRes.status()} path=${PLAYER_WITHDRAW_REQUEST_PATH} body=${reqText}`
      );
    }

    const txFromResponse = reqJson?.transaction || reqJson?.data?.transaction || reqJson;
    const txId = txFromResponse?.id || txFromResponse?.tx_id;

    if (!txId) {
      throw new Error(`withdraw request response missing tx_id: ${JSON.stringify(reqJson)}`);
    }

    // 4) Admin listeden tx’i bul ve requested olduğunu doğrula
    const list1 = await adminListWithdrawals(BACKEND_URL, ownerToken, {
      state: 'requested',
      limit: 50,
      offset: 0,
    });

    const items1: any[] = list1.items || list1.data?.items || [];
    const w1 = items1.find((x) => x.tx_id === txId || x.id === txId);

    expect(w1, 'requested withdrawal must appear in admin list').toBeTruthy();
    expect(w1.state).toBe('requested');

    const balanceAfterRequested = w1.balance_after;

    // 5) Approve
    const approveRes = await adminApprove(BACKEND_URL, ownerToken, txId);
    if (!approveRes.ok()) {
      const body = await approveRes.text();
      throw new Error(`approve failed ${approveRes.status()} body=${body}`);
    }

    // 6) Approve sonrası state=approved doğrula
    const list2 = await adminListWithdrawals(BACKEND_URL, ownerToken, {
      state: 'approved',
      limit: 50,
      offset: 0,
    });
    const items2: any[] = list2.items || list2.data?.items || [];
    const w2 = items2.find((x) => x.tx_id === txId || x.id === txId);

    expect(w2, 'approved withdrawal must appear in admin list').toBeTruthy();
    expect(w2.state).toBe('approved');

    if (balanceAfterRequested !== undefined && w2.balance_after !== undefined) {
      expect(w2.balance_after).toBe(balanceAfterRequested);
    }

    // 7) Mark paid
    const paidRes = await adminMarkPaid(BACKEND_URL, ownerToken, txId);
    if (!paidRes.ok()) {
      const body = await paidRes.text();
      throw new Error(`mark-paid failed ${paidRes.status()} body=${body}`);
    }

    // 8) paid state doğrula
    const list3 = await adminListWithdrawals(BACKEND_URL, ownerToken, {
      state: 'paid',
      limit: 50,
      offset: 0,
    });
    const items3: any[] = list3.items || list3.data?.items || [];
    const w3 = items3.find((x) => x.tx_id === txId || x.id === txId);

    expect(w3, 'paid withdrawal must appear in admin list').toBeTruthy();
    expect(w3.state).toBe('paid');

    // 9) Negatif: paid olduktan sonra tekrar approve etmeye çalış → 409 bekle
    const approveAgainRes = await adminApprove(BACKEND_URL, ownerToken, txId);
    expect(approveAgainRes.status(), 'second approve should be invalid transition').toBe(409);

    // UI tarafında da satırın göründüğünü basitçe doğrula (smoke olarak yeterli)
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.getByText(txId)).toBeVisible();
  });
});
