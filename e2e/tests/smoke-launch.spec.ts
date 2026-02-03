import { test, expect, request as pwRequest } from '@playwright/test';

const API_BASE = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || process.env.OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || process.env.OWNER_PASSWORD || 'Admin123!';

async function apiLogin(ctx: any, email: string, password: string) {
  const res = await ctx.post('/api/v1/auth/login', { data: { email, password } });
  const text = await res.text();
  expect(res.ok(), `admin login failed ${res.status()} body=${text}`).toBeTruthy();
  const json = JSON.parse(text);
  const token = json.access_token || json.token;
  const admin = json.admin || json.user || json.data?.admin;
  expect(token).toBeTruthy();
  expect(admin).toBeTruthy();
  return { token, admin };
}

async function registerPlayer(ctx: any, email: string, password: string) {
  const res = await ctx.post('/api/v1/auth/player/register', {
    data: {
      email,
      username: email.split('@')[0],
      password,
      tenant_id: 'default_casino',
    },
  });
  const text = await res.text();
  expect(res.ok(), `player register failed ${res.status()} body=${text}`).toBeTruthy();
  const json = JSON.parse(text);
  const playerId = json.player_id;
  expect(playerId).toBeTruthy();
  return playerId;
}

async function approveKyc(ctx: any, ownerToken: string, playerId: string) {
  const res = await ctx.post(`/api/v1/kyc/documents/${playerId}/review`, {
    headers: { Authorization: `Bearer ${ownerToken}` },
    data: { status: 'approved' },
  });
  const text = await res.text();
  expect(res.ok(), `KYC approve failed ${res.status()} body=${text}`).toBeTruthy();
}

async function playerLogin(ctx: any, email: string, password: string) {
  const res = await ctx.post('/api/v1/auth/player/login', {
    data: { email, password, tenant_id: 'default_casino' },
  });
  const text = await res.text();
  expect(res.ok(), `player login failed ${res.status()} body=${text}`).toBeTruthy();
  const json = JSON.parse(text);
  const token = json.access_token || json.token;
  expect(token).toBeTruthy();
  return token;
}

async function createPendingWithdrawal(ctx: any, ownerToken: string) {
  const unique = Date.now();
  const email = `smoke_${unique}@casino.com`;
  const password = 'Test123!';

  const playerId = await registerPlayer(ctx, email, password);
  await approveKyc(ctx, ownerToken, playerId);

  const playerToken = await playerLogin(ctx, email, password);

  const depRes = await ctx.post('/api/v1/player/wallet/deposit', {
    headers: {
      Authorization: `Bearer ${playerToken}`,
      'Idempotency-Key': `smoke-dep-${unique}`,
    },
    data: { amount: 50, method: 'test' },
  });
  const depText = await depRes.text();
  expect(depRes.ok(), `deposit failed ${depRes.status()} body=${depText}`).toBeTruthy();

  const wdRes = await ctx.post('/api/v1/player/wallet/withdraw', {
    headers: {
      Authorization: `Bearer ${playerToken}`,
      'Idempotency-Key': `smoke-wd-${unique}`,
    },
    data: { amount: 20, method: 'test_bank', address: 'smoke' },
  });
  const wdText = await wdRes.text();
  expect(wdRes.ok(), `withdraw failed ${wdRes.status()} body=${wdText}`).toBeTruthy();
  const wdJson = JSON.parse(wdText);
  const withdrawalId = wdJson?.transaction?.id;
  expect(withdrawalId).toBeTruthy();

  return { withdrawalId };
}

test.describe('P0 Launch Smoke (Golden Path)', () => {
  test.setTimeout(180000);

  test('Login -> Import Game -> Approve Withdrawal -> Logout', async ({ browser }) => {
    const api = await pwRequest.newContext({ baseURL: API_BASE });
    const { token: ownerToken } = await apiLogin(api, OWNER_EMAIL, OWNER_PASSWORD);

    const { withdrawalId } = await createPendingWithdrawal(api, ownerToken);

    const context = await browser.newContext({ baseURL: FRONTEND_URL });
    const page = await context.newPage();

    await page.goto('/login', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('login-email-input').fill(OWNER_EMAIL);
    await page.getByTestId('login-password-input').fill(OWNER_PASSWORD);
    await page.getByTestId('login-submit-button').click();
    await expect(page).toHaveURL(/\/$/, { timeout: 30000 });

    await page.goto('/games', { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: 'Upload' }).click();
    await page.getByText('Method').locator('xpath=following::button[@role="combobox"][1]').click();
    await page.getByRole('option', { name: 'Upload HTML5 Game Bundle' }).click();
    await page.getByRole('button', { name: 'HTML5' }).click();
    await page.locator('input[type="file"]').first().setInputFiles('fixtures/demo_games.json');
    await page.getByRole('button', { name: 'Upload & Analyze' }).click();
    await expect(page.getByText('Import Preview', { exact: true })).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: 'İçe Aktarmayı Başlat' }).click();
    await page.getByRole('tab', { name: 'Slots' }).click();
    await expect(page.getByText('Demo Game 101')).toBeVisible({ timeout: 30000 });

    await page.goto('/finance/withdrawals', { waitUntil: 'domcontentloaded' });
    const row = page.locator('tr', { hasText: withdrawalId });
    await expect(row).toBeVisible({ timeout: 30000 });
    await row.getByRole('button', { name: 'Approve' }).click();
    await page.locator('#action-reason').fill('Smoke approval');
    await page.getByRole('button', { name: 'Confirm' }).click();
    await expect(row).toContainText('Approved', { timeout: 30000 });

    await page.getByTestId('sidebar-logout-button').click();
    await expect(page).toHaveURL(/\/login/, { timeout: 20000 });

    await context.close();
    await api.dispose();
  });
});
