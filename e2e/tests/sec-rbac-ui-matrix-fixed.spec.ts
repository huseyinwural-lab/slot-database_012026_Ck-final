import { test, expect, request as pwRequest } from '@playwright/test';

const API_BASE = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';

const OWNER_EMAIL = process.env.OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.OWNER_PASSWORD || 'Admin123!';
const DEFAULT_PASSWORD = process.env.E2E_ROLE_PASSWORD || 'Admin123!';

async function apiLogin(ctx: any, email: string, password: string) {
  const res = await ctx.post('/api/v1/auth/login', { data: { email, password } });
  const text = await res.text();
  expect(res.ok(), `login failed ${res.status()} body=${text}`).toBeTruthy();
  const json = JSON.parse(text);
  const token = json.access_token || json.token;
  const admin = json.admin || json.user || json.data?.admin;
  expect(token).toBeTruthy();
  expect(admin).toBeTruthy();
  return { token, admin };
}

async function ensureAdminUser(ownerCtx: any, ownerToken: string, email: string, role: string, fullName: string) {
  const listRes = await ownerCtx.get('/api/v1/admin/users', {
    headers: { Authorization: `Bearer ${ownerToken}` },
  });
  if (listRes.ok()) {
    const users = await listRes.json();
    const exists = (users || []).some((u: any) => (u.email || '').toLowerCase() === email.toLowerCase());
    if (exists) return;
  }

  // Create if missing
  const createRes = await ownerCtx.post('/api/v1/admin/users', {
    headers: { Authorization: `Bearer ${ownerToken}` },
    data: {
      email,
      password_mode: 'set',
      password: DEFAULT_PASSWORD,
      full_name: fullName,
      role,
    },
  });

  // If it already exists due to race, it's fine.
  if (!createRes.ok()) {
    const body = await createRes.text();
    // Accept "already exists" type errors
    if (!body.toLowerCase().includes('exists')) {
      throw new Error(`ensureAdminUser create failed ${createRes.status()} body=${body}`);
    }
  }
}

async function openFirstPlayerDrawer(page: any) {
  await page.goto(`${FRONTEND_URL}/players`);
  await page.waitForTimeout(1000);

  // Use a working selector instead of the test ID
  const openBtn = page.locator('table tbody tr td:last-child button').first();
  await expect(openBtn).toBeVisible({ timeout: 20000 });
  await openBtn.click({ force: true });

  await expect(page.getByText('Player Actions', { exact: true })).toBeVisible({ timeout: 10000 });
}

async function injectAdminSession(page: any, token: string, admin: any) {
  await page.addInitScript(
    ({ t, u }) => {
      window.localStorage.setItem('admin_token', t);
      window.localStorage.setItem('admin_user', JSON.stringify(u));
    },
    { t: token, u: admin }
  );
}

const MATRIX = [
  {
    name: 'Super Admin',
    email: OWNER_EMAIL,
    password: OWNER_PASSWORD,
    expectCredit: true,
    expectOps: true,
  },
  {
    name: 'Tenant Admin (drift)',
    email: 'admin_user@casino.com',
    password: DEFAULT_PASSWORD,
    expectCredit: true,
    expectOps: true,
  },
  {
    name: 'Ops',
    email: 'ops@casino.com',
    password: DEFAULT_PASSWORD,
    expectCredit: false,
    expectOps: true,
  },
  {
    name: 'Support',
    email: 'support@casino.com',
    password: DEFAULT_PASSWORD,
    expectCredit: false,
    expectOps: false,
  },
];

test.describe('SEC-P0-02 UI RBAC Matrix (PlayerActionsDrawer) - Fixed', () => {
  test.setTimeout(120000);

  test.beforeAll(async () => {
    const ctx = await pwRequest.newContext({ baseURL: API_BASE });
    const { token: ownerToken } = await apiLogin(ctx, OWNER_EMAIL, OWNER_PASSWORD);

    await ensureAdminUser(ctx, ownerToken, 'admin_user@casino.com', 'Tenant Admin', 'Tenant Admin');
    await ensureAdminUser(ctx, ownerToken, 'ops@casino.com', 'Ops', 'Ops User');
    await ensureAdminUser(ctx, ownerToken, 'support@casino.com', 'Support', 'Support User');
  });

  for (const row of MATRIX) {
    test(`${row.name}: button visibility`, async ({ browser }) => {
      const api = await pwRequest.newContext({ baseURL: API_BASE });
      const { token, admin } = await apiLogin(api, row.email, row.password);

      const context = await browser.newContext();
      const page = await context.newPage();
      await injectAdminSession(page, token, admin);

      await openFirstPlayerDrawer(page);

      const creditBtn = page.getByTestId('player-action-credit');
      const debitBtn = page.getByTestId('player-action-debit');
      const bonusBtn = page.getByTestId('player-action-bonus');

      const suspendBtn = page.getByTestId('player-action-suspend');
      const unsuspendBtn = page.getByTestId('player-action-unsuspend');
      const forceLogoutBtn = page.getByTestId('player-action-force-logout');

      if (row.expectCredit) {
        await expect(creditBtn).toBeVisible();
        await expect(debitBtn).toBeVisible();
        await expect(bonusBtn).toBeVisible();
      } else {
        await expect(creditBtn).toHaveCount(0);
        await expect(debitBtn).toHaveCount(0);
        await expect(bonusBtn).toHaveCount(0);
      }

      if (row.expectOps) {
        await expect(suspendBtn).toBeVisible();
        await expect(unsuspendBtn).toBeVisible();
        await expect(forceLogoutBtn).toBeVisible();
      } else {
        await expect(suspendBtn).toHaveCount(0);
        await expect(unsuspendBtn).toHaveCount(0);
        await expect(forceLogoutBtn).toHaveCount(0);
      }

      await context.close();
    });
  }
});