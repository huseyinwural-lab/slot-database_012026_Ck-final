import { test, expect } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';

async function login(page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(OWNER_EMAIL);
  await page.getByLabel('Password').fill(OWNER_PASSWORD);
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/\/$/);
}

async function setTenant(page, tenantId: string) {
  // App reads this and sends X-Tenant-ID header via axios interceptor
  await page.evaluate((tid) => {
    localStorage.setItem('impersonate_tenant_id', tid);
  }, tenantId);
}

async function waitForApiResponse(page, urlPart: string) {
  return page.waitForResponse((r) => r.url().includes(urlPart), { timeout: 20_000 });
}

test.describe('CRM + Affiliates smoke (minimal/full tenant matrix)', () => {
  test('default_casino (full): CRM loads and initial request 200', async ({ page }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    const respPromise = waitForApiResponse(page, '/api/v1/crm/campaigns');
    await page.goto('/crm');

    const resp = await respPromise;
    expect(resp.status(), await resp.text()).toBe(200);
    await expect(page.getByRole('heading', { name: /crm/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);
  });

  test('default_casino (full): Affiliates loads and initial request 200', async ({ page }) => {
    await login(page);
    await setTenant(page, 'default_casino');

    const respPromise = waitForApiResponse(page, '/api/v1/affiliates');
    await page.goto('/affiliates');

    const resp = await respPromise;
    expect(resp.status(), await resp.text()).toBe(200);
    await expect(page.getByRole('heading', { name: /affiliate/i })).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);
  });

  test('demo_renter (minimal): CRM shows ModuleDisabled and API is 403/503', async ({ page }) => {
    await login(page);
    await setTenant(page, 'demo_renter');

    const respPromise = waitForApiResponse(page, '/api/v1/crm/campaigns');
    await page.goto('/crm');

    const resp = await respPromise;
    expect([403, 503]).toContain(resp.status());
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);
  });

  test('demo_renter (minimal): Affiliates shows ModuleDisabled and API is 403/503', async ({ page }) => {
    await login(page);
    await setTenant(page, 'demo_renter');

    const respPromise = waitForApiResponse(page, '/api/v1/affiliates');
    await page.goto('/affiliates');

    const resp = await respPromise;
    expect([403, 503]).toContain(resp.status());
    await expect(page.getByText(/module disabled/i)).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);
  });
});
