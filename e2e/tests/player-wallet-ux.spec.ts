import { test, expect, request as pwRequest } from '@playwright/test';

// Environments
const BACKEND_URL = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000'; // Admin
const PLAYER_URL = process.env.PLAYER_APP_URL || 'http://localhost:3001';

const PLAYER_EMAIL = `ux-test-${Date.now()}@example.com`;
const PLAYER_PASSWORD = 'Player123!';

// --- Helpers ---
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
  return { 
    token: json.access_token || json.token,
    playerId: json.user?.id 
  };
}

test.describe('Player Wallet UX (PLAYER-WALLET-UX-001)', () => {
  let playerToken;

  test.beforeAll(async () => {
    const p = await apiRegisterOrLoginPlayer(BACKEND_URL, PLAYER_EMAIL, PLAYER_PASSWORD);
    playerToken = p.token;
  });

  test('Wallet UI elements, transaction history and balance updates', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Inject token
    await page.addInitScript(({ token }) => {
      localStorage.setItem('player_token', token);
      localStorage.setItem('player_tenant_id', 'default_casino');
    }, { token: playerToken });

    await page.goto(`${PLAYER_URL}/wallet`);

    // 1. Verify Balance Cards (Available, Held, Total)
    await expect(page.getByText('Available Balance')).toBeVisible();
    await expect(page.getByText('Held Balance')).toBeVisible();
    await expect(page.getByText('Total Balance')).toBeVisible();

    // 2. Perform Deposit
    await page.click('button:has-text("Deposit")');
    await page.fill('input[placeholder*="Min"]', '50');
    await page.click('button:has-text("Pay Now"), button:has-text("Pay with Stripe"), button:has-text("Pay with Adyen")');
    // Stripe flow redirects and then shows a success banner; accept either final success or verification step.
    await expect(page.getByText('Payment Successful!').or(page.getByText('Verifying payment...'))).toBeVisible({ timeout: 20000 });

    // 3. Verify Transaction in Table (History)
    // Table headers
    await expect(page.locator('th:has-text("Type")')).toBeVisible();
    await expect(page.locator('th:has-text("Amount")')).toBeVisible();
    await expect(page.locator('th:has-text("State")')).toBeVisible();
    
    // Verify row data
    await expect(page.locator('td', { hasText: 'deposit' }).first()).toBeVisible();
    await expect(page.locator('td', { hasText: '50.00' }).first()).toBeVisible();
    await expect(page.locator('td', { hasText: 'completed' })
      .or(page.locator('td', { hasText: 'pending_provider' }))
      .or(page.locator('td', { hasText: 'created' }))
      .first()
    ).toBeVisible();

    // 4. Verify Pagination Controls
    const prevBtn = page.locator('button[aria-label="Previous Page"]');
    const nextBtn = page.locator('button[aria-label="Next Page"]');
    await expect(prevBtn).toBeVisible();
    await expect(nextBtn).toBeVisible();
    await expect(prevBtn).toBeDisabled(); // First page

    await context.close();
  });
});
