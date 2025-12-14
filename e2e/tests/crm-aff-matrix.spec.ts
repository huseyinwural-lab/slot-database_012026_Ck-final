import { test, expect } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';

// Used by APIRequestContext (bypasses UI flakiness for status checks)
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8001';

async function login(page: any) {
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

test.describe('CRM + Affiliates smoke (minimal/full tenant matrix)', () => {
  test('default_casino (full): CRM loads + campaigns API 200', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    // UI
    await page.goto('/crm');
    await expect(page.getByRole('heading', { name: /crm/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    // API (deterministic)
    const res = await request.get(`${API_BASE}/api/v1/crm/campaigns`, {
      headers: { 'X-Tenant-ID': 'default_casino' },
    });
    expect(res.status()).toBe(200);
  });

  test('default_casino (full): Affiliates loads + list API 200', async ({ page, request }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    await page.goto('/affiliates');
    await expect(page.getByRole('heading', { name: /affiliate/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const res = await request.get(`${API_BASE}/api/v1/affiliates/`, {
      headers: { 'X-Tenant-ID': 'default_casino' },
    });
    expect(res.status()).toBe(200);
  });

  test('demo_renter (minimal): CRM gated + campaigns API 403/503', async ({ page, request }) => {
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

  test('demo_renter (minimal): Affiliates gated + list API 403/503', async ({ page, request }) => {
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
