import { test, expect } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';

// Used by APIRequestContext (deterministic status checks)
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8001';

async function uiLogin(page: any) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(OWNER_EMAIL);
  await page.getByLabel('Password').fill(OWNER_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();

  // Login uses window.location.href (full reload)
  await page.waitForLoadState('domcontentloaded');
  await expect(page).toHaveURL(/\/$/);
}

async function setTenant(page: any, tenantId: string) {
  await page.evaluate((tid: string) => {
    localStorage.setItem('impersonate_tenant_id', tid);
  }, tenantId);
}

async function apiToken(request: any): Promise<string> {
  const res = await request.post(`${API_BASE}/api/v1/auth/login`, {
    data: { email: OWNER_EMAIL, password: OWNER_PASSWORD },
  });
  expect(res.status(), await res.text()).toBe(200);
  const json = await res.json();
  return json.access_token;
}

async function apiGet(request: any, path: string, tenantId: string, token: string) {
  return request.get(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Tenant-ID': tenantId,
    },
  });
}

test.describe('CRM + Affiliates smoke (minimal/full tenant matrix)', () => {
  test('default_casino (full): CRM loads + campaigns API 200', async ({ page, request }) => {
    await uiLogin(page);
    await setTenant(page, 'default_casino');

    // UI
    await page.goto('/crm');
    await expect(page.getByRole('heading', { name: /crm/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    // API
    const token = await apiToken(request);
    const res = await apiGet(request, '/api/v1/crm/campaigns', 'default_casino', token);
    expect(res.status(), await res.text()).toBe(200);
  });

  test('default_casino (full): Affiliates loads + list API 200', async ({ page, request }) => {
    await uiLogin(page);
    await setTenant(page, 'default_casino');

    await page.goto('/affiliates');
    await expect(page.getByRole('heading', { name: /affiliate/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const token = await apiToken(request);
    const res = await apiGet(request, '/api/v1/affiliates/', 'default_casino', token);
    expect(res.status(), await res.text()).toBe(200);
  });

  test('demo_renter (minimal): CRM gated + campaigns API 403/503', async ({ page, request }) => {
    await uiLogin(page);
    await setTenant(page, 'demo_renter');

    await page.goto('/crm');
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const token = await apiToken(request);
    const res = await apiGet(request, '/api/v1/crm/campaigns', 'demo_renter', token);
    expect([403, 503]).toContain(res.status());
  });

  test('demo_renter (minimal): Affiliates gated + list API 403/503', async ({ page, request }) => {
    await uiLogin(page);
    await setTenant(page, 'demo_renter');

    await page.goto('/affiliates');
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const token = await apiToken(request);
    const res = await apiGet(request, '/api/v1/affiliates/', 'demo_renter', token);
    expect([403, 503]).toContain(res.status());
  });
});
