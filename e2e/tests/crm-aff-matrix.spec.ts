import { test, expect } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8001';

async function login(page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(OWNER_EMAIL);
  await page.getByLabel('Password').fill(OWNER_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();

  // Login triggers a hard reload via window.location.href
  await page.wait_for_load_state('domcontentloaded');
  await expect(page).to_have_url(/\/$/);
}

async function setTenant(page, tenantId: string) {
  // App reads this and sends X-Tenant-ID header via axios interceptor
  await page.evaluate((tid) => {
    localStorage.setItem('impersonate_tenant_id', tid);
  }, tenantId);
}

async function assertApiStatus(request, path: string, status: number, tenantId: string) {
  const res = await request.get(`${API_BASE}${path}`, {
    headers: {
      'X-Tenant-ID': tenantId,
    },
  });
  expect(res.status()).toBe(status);
}

test.describe('CRM + Affiliates smoke (minimal/full tenant matrix)', () => {
  test('default_casino (full): CRM loads + campaigns API 200', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    // UI
    await page.goto('/crm');
    await expect(page.getByRole('heading', { name: /crm/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    // API (deterministic)
    await assertApiStatus(request, '/api/v1/crm/campaigns', 200, 'default_casino');
  });

  test('default_casino (full): Affiliates loads + list API 200', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    await page.goto('/affiliates');
    await expect(page.getByRole('heading', { name: /affiliate/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    await assertApiStatus(request, '/api/v1/affiliates/', 200, 'default_casino');
  });

  test('demo_renter (minimal): CRM is gated (ModuleDisabled) + campaigns API 403/503', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'demo_renter');

    await page.goto('/crm');
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const res = await request.get(`${API_BASE}/api/v1/crm/campaigns`, {
      headers: { 'X-Tenant-ID': 'demo_renter' },
    });
    expect([403, 503]).toContain(res.status());
  });

  test('demo_renter (minimal): Affiliates is gated (ModuleDisabled) + list API 403/503', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'demo_renter');

    await page.goto('/affiliates');
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const res = await request.get(`${API_BASE}/api/v1/affiliates/`, {
      headers: { 'X-Tenant-ID': 'demo_renter' },
    });
    expect([403, 503]).toContain(res.status());
  });
});
