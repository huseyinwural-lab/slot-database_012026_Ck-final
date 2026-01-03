import { test, expect, request as pwRequest } from '@playwright/test';

// Environments
const BACKEND_URL = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';
const PLAYER_URL = process.env.PLAYER_APP_URL || 'http://localhost:3001'; // Assuming default

const LS_TOKEN_KEY = 'admin_token';
const LS_PLAYER_TOKEN_KEY = 'player_token';

const OWNER_EMAIL = process.env.OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.OWNER_PASSWORD || 'Admin123!';

const PLAYER_EMAIL = `policy-test-player-${Date.now()}@example.com`;
const PLAYER_PASSWORD = 'Player123!';

// --- Helpers ---

async function apiLoginAdmin(apiBaseUrl, email, password) {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });
  const res = await ctx.post('/api/v1/auth/login', {
    data: { email, password },
  });
  if (!res.ok()) throw new Error(`Admin login failed: ${res.status()}`);
  const json = await res.json();
  return json.access_token || json.token;
}

async function apiRegisterOrLoginPlayer(apiBaseUrl, email, password) {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });
  let res = await ctx.post('/api/v1/auth/player/login', {
    data: { email, password, tenant_id: 'default_casino' },
  });

  if (res.status() === 401) {
    const username = email.split('@')[0];
    await ctx.post('/api/v1/auth/player/register', {
      data: { email, password, username, tenant_id: 'default_casino' },
    });
    res = await ctx.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: 'default_casino' },
    });
  }
  if (!res.ok()) throw new Error(`Player auth failed: ${res.status()}`);
  const json = await res.json();
  const token = json.access_token || json.token;
  const playerId = json.player_id || json.user?.id;
  return { token, playerId };
}

async function apiApproveKyc(apiBaseUrl, adminToken, playerId) {
  const ctx = await pwRequest.newContext({
    baseURL: apiBaseUrl,
    extraHTTPHeaders: { Authorization: `Bearer ${adminToken}` },
  });
  await ctx.post(`/api/v1/kyc/documents/${playerId}/review`, {
    data: { status: 'approved' },
  });
}

// --- Tests ---

test.describe('Tenant Policy Limits (E2E-POLICY-001)', () => {
  test.describe.configure({ mode: 'serial' });

  let adminToken;
  let playerToken;
  let playerId;

  test.beforeAll(async () => {
    adminToken = await apiLoginAdmin(BACKEND_URL, OWNER_EMAIL, OWNER_PASSWORD);
    const p = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);
    playerToken = p.token;
    playerId = p.playerId;
    // Approve KYC for withdraws
    await apiApproveKyc(BACKEND_URL, adminToken, playerId);
  });

  test('Deposit limit exceeded enforcement', async ({ browser }) => {
    // 1. Admin: Set daily_deposit_limit = 50 via UI
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.addInitScript(({ key, token }) => {
      localStorage.setItem(key, token);
    }, { key: LS_TOKEN_KEY, token: adminToken });

    // Debug console
    adminPage.on('console', msg => console.log('PAGE LOG:', msg.text()));
    adminPage.on('requestfailed', req => console.log('REQ FAILED:', req.url(), req.failure().errorText));
    adminPage.on('response', resp => console.log('RESP:', resp.url(), resp.status()));

    await adminPage.goto(`${FRONTEND_URL}/settings`);
    // Find Payments Policy tab and wait for response
    await Promise.all([
      adminPage.waitForResponse(resp => resp.url().includes('/policy') && resp.status() === 200),
      adminPage.click('button[role="tab"]:has-text("Payments Policy")')
    ]);
    
    // Wait for React to process the response
    await adminPage.waitForTimeout(1000);
    // Wait for input to be visible to ensure tab content loaded
    const depositInput = adminPage.locator('text=Daily Deposit Limit').locator('xpath=..').locator('input');
    await expect(depositInput).toBeVisible();

    // Fill limit
    await depositInput.fill('50');
    await expect(depositInput).toHaveValue('50');
    
    const saveButton = adminPage.locator('button:has-text("Kaydet")');
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();

    // Save with response wait
    const [response] = await Promise.all([
      adminPage.waitForResponse(resp => resp.url().includes('/policy') && resp.status() === 200),
      saveButton.click({ force: true })
    ]);
    
    await expect(adminPage.getByText('Payments policy kaydedildi')).toBeVisible();
    await adminContext.close();

    // 2. Player: Deposit 40 (Success) via UI
    const playerContext = await browser.newContext();
    const playerPage = await playerContext.newPage();
    await playerPage.addInitScript(({ key, token }) => {
      localStorage.setItem(key, token);
    }, { key: LS_PLAYER_TOKEN_KEY, token: playerToken });

    await playerPage.goto(`${PLAYER_URL}/wallet`);
    
    // Click Deposit tab if needed (default)
    await playerPage.click('button:has-text("Deposit")');
    
    // Input 40
    await playerPage.fill('input[placeholder*="Min"]', '40');
    await playerPage.click('button:has-text("Pay Now"), button:has-text("Pay with Stripe"), button:has-text("Pay with Adyen")');
    
    // Stripe flow redirects and then shows a success banner; accept either final success or verification step.
    await expect(playerPage.getByText('Payment Successful!').or(playerPage.getByText('Verifying payment...'))).toBeVisible({ timeout: 20000 });

    // 3. Player: Deposit 20 (Fail: 40+20 > 50) via UI
    // Reload to clear success message/state if needed
    await playerPage.reload();
    await playerPage.fill('input[placeholder*="Min"]', '20');
    await playerPage.click('button:has-text("Pay Now"), button:has-text("Pay with Stripe"), button:has-text("Pay with Adyen")');

    // Assert Failure
    await expect(playerPage.getByText(/limit/i)).toBeVisible(); // Matches 'Günlük işlem limiti aşıldı.'
    // Ideally verify network response too, but UI check satisfies requirement
    
    await playerContext.close();
  });

  test('Withdraw limit exceeded enforcement', async ({ browser }) => {
    // 1. Admin: Set daily_withdraw_limit = 30 via UI
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.addInitScript(({ key, token }) => {
      localStorage.setItem(key, token);
    }, { key: LS_TOKEN_KEY, token: adminToken });

    // Debug
    adminPage.on('console', msg => console.log('PAGE LOG:', msg.text()));

    await adminPage.goto(`${FRONTEND_URL}/settings`);
    
    // Click tab and wait for response
    await Promise.all([
      adminPage.waitForResponse(resp => resp.url().includes('/policy') && resp.status() === 200),
      adminPage.click('button[role="tab"]:has-text("Payments Policy")')
    ]);
    
    // Wait for React to process the response
    await adminPage.waitForTimeout(1000);
    
    // Wait for input
    const withdrawInput = adminPage.locator('text=Daily Withdraw Limit').locator('xpath=..').locator('input');
    await expect(withdrawInput).toBeVisible();

    // Fill limit
    await withdrawInput.fill('30');
    await expect(withdrawInput).toHaveValue('30');
    
    const saveButton = adminPage.locator('button:has-text("Kaydet")');
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();

    // Save with response wait
    const [response] = await Promise.all([
      adminPage.waitForResponse(resp => resp.url().includes('/policy') && resp.status() === 200),
      saveButton.click({ force: true })
    ]);

    await expect(adminPage.getByText('Payments policy kaydedildi')).toBeVisible();
    await adminContext.close();

    // 2. Player: Deposit 100 (Success) to fund wallet
    // We can do this via API to speed up
    const pCtx = await pwRequest.newContext({ baseURL: BACKEND_URL, extraHTTPHeaders: { Authorization: `Bearer ${playerToken}` } });
    await pCtx.post('/api/v1/player/wallet/deposit', { data: { amount: 100, method: 'test' }, headers: { 'Idempotency-Key': `setup-${Date.now()}` } });

    // 3. Player: Withdraw 20 (Success) via UI
    const playerContext = await browser.newContext();
    const playerPage = await playerContext.newPage();
    await playerPage.addInitScript(({ key, token }) => {
      localStorage.setItem(key, token);
    }, { key: LS_PLAYER_TOKEN_KEY, token: playerToken });

    await playerPage.goto(`${PLAYER_URL}/wallet`);
    
    // Switch to Withdraw tab
    await playerPage.click('button:has-text("Withdraw")');
    
    // Input 20
    await playerPage.fill('input[placeholder*="Max"]', '20');
    await playerPage.fill('input[placeholder*="TR"]', 'test-iban');
    await playerPage.click('button:has-text("Request Payout")');
    
    // Assert Success
    await expect(playerPage.getByText('Withdrawal requested successfully')).toBeVisible();

    // 4. Player: Withdraw 15 (Fail: 20+15 > 30) via UI
    await playerPage.reload();
    await playerPage.click('button:has-text("Withdraw")');
    await playerPage.fill('input[placeholder*="Max"]', '15');
    await playerPage.fill('input[placeholder*="TR"]', 'test-iban-2');
    await playerPage.click('button:has-text("Request Payout")');

    // Assert Failure
    await expect(playerPage.getByText(/limit/i)).toBeVisible();
    
    await playerContext.close();
  });
});
