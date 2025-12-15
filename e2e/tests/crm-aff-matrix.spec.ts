import { test, expect } from '@playwright/test';

// --- CONFIGURATION ---
const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || 'Admin123!';
const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8001';

// --- ROBUST HELPER FUNCTIONS ---

/**
 * Performs a robust UI login by waiting for network response and subsequent navigation.
 */
async function robustLogin(page: any) {
  await page.goto('/login');

  // Fill credentials
  await page.getByLabel('Email').fill(OWNER_EMAIL);
  await page.getByLabel('Password').fill(OWNER_PASSWORD);

  // Setup wait for the login API response BEFORE clicking
  const loginResponsePromise = page.waitForResponse((response: any) => 
    response.url().includes('/auth/login') && response.request().method() === 'POST'
  );

  // Click Sign In
  await page.getByRole('button', { name: /sign in/i }).click();

  // Wait for the API response
  const response = await loginResponsePromise;
  
  // Debug: If login fails, log it
  if (response.status() !== 200) {
    const body = await response.text();
    console.error(`[Login Failed] Status: ${response.status()}, Body: ${body}`);
    throw new Error(`Login API failed with status ${response.status()}`);
  }

  // Wait for navigation to Dashboard (root)
  // This waits for the URL to change from /login to /
  await page.waitForURL(/\/$/, { timeout: 15000 });

  // Explicitly wait for a Dashboard element to ensure app is interactive
  await expect(page.getByText('Dashboard', { exact: true }).first()).toBeVisible({ timeout: 10000 });
}

/**
 * Switches tenant context using the developer/impersonation feature.
 * This simulates the behavior of the TenantSwitcher component or local storage override.
 */
async function setTenantContext(page: any, tenantId: string) {
  // Use evaluate to access localStorage directly in the browser context
  await page.evaluate((tid: string) => {
    localStorage.setItem('impersonate_tenant_id', tid);
    // Dispatch a storage event or reload might be needed depending on app implementation
    // For this app, we reload to ensure headers are picked up by the API client
  }, tenantId);
  
  await page.reload();
  // Wait for dashboard to settle again after reload
  await expect(page.getByText('Dashboard', { exact: True }).first()).toBeVisible();
}

/**
 * Gets a fresh API token for direct API testing
 */
async function getApiToken(request: any): Promise<string> {
  const res = await request.post(`${API_BASE}/api/v1/auth/login`, {
    data: { email: OWNER_EMAIL, password: OWNER_PASSWORD },
  });
  expect(res.status(), `API Login failed: ${await res.text()}`).toBe(200);
  const json = await res.json();
  return json.access_token;
}

// --- TEST SUITE ---

test.describe('CRM + Affiliates Matrix (Robust)', () => {
  
  // 1. DEFAULT CASINO (Full Features)
  test('default_casino: CRM loads correctly', async ({ page, request }) => {
    await robustLogin(page);
    await setTenantContext(page, 'default_casino');

    // UI Check
    await page.goto('/crm');
    // Expect CRM specific header or content
    await expect(page.getByRole('heading', { name: /CRM/i }).first()).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    // API Check (Double check backend access)
    const token = await getApiToken(request);
    const res = await request.get(`${API_BASE}/api/v1/crm/campaigns`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': 'default_casino' }
    });
    expect(res.status()).toBe(200);
  });

  test('default_casino: Affiliates loads correctly', async ({ page, request }) => {
    await robustLogin(page);
    await setTenantContext(page, 'default_casino');

    await page.goto('/affiliates');
    await expect(page.getByRole('heading', { name: /Affiliate/i }).first()).toBeVisible();
    await expect(page.getByText(/load failed/i)).toHaveCount(0);

    const token = await getApiToken(request);
    const res = await request.get(`${API_BASE}/api/v1/affiliates/`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': 'default_casino' }
    });
    expect(res.status()).toBe(200);
  });

  // 2. DEMO RENTER (Minimal Features - Should be Gated)
  test('demo_renter: CRM is disabled/gated', async ({ page, request }) => {
    await robustLogin(page);
    await setTenantContext(page, 'demo_renter');

    await page.goto('/crm');
    // Expect specific "Module Disabled" or "Access Denied" UI
    // If exact text varies, we look for key indicators or absence of main content
    // Assuming the app shows a "Module Disabled" component or redirects
    const moduleDisabledText = page.getByText(/module disabled|access denied|feature not available/i);
    await expect(moduleDisabledText.first()).toBeVisible();

    const token = await getApiToken(request);
    const res = await request.get(`${API_BASE}/api/v1/crm/campaigns`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': 'demo_renter' }
    });
    // Should be 403 Forbidden or 503 Service Unavailable (depending on implementation)
    expect([403, 503]).toContain(res.status());
  });

  test('demo_renter: Affiliates is disabled/gated', async ({ page, request }) => {
    await robustLogin(page);
    await setTenantContext(page, 'demo_renter');

    await page.goto('/affiliates');
    const moduleDisabledText = page.getByText(/module disabled|access denied|feature not available/i);
    await expect(moduleDisabledText.first()).toBeVisible();

    const token = await getApiToken(request);
    const res = await request.get(`${API_BASE}/api/v1/affiliates/`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Tenant-ID': 'demo_renter' }
    });
    expect([403, 503]).toContain(res.status());
  });

});
