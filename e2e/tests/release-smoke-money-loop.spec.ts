import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Release Smoke Money Loop (Deterministic)', () => {
  test.setTimeout(90000); 

  test('Full Cycle: Deposit -> Withdraw -> Admin Payout -> Paid', async ({ page, browser }) => {
    const PLAYER_APP_URL = 'http://localhost:3001';
    const ADMIN_APP_URL = 'http://localhost:3000';
    const API_URL = 'http://localhost:8001';

    // === DATA SETUP ===
    const uniqueId = Date.now();
    const email = `rc_${uniqueId}@example.com`;
    const password = 'Password123!';
    const tenantId = 'default_casino';

    // Register Player
    const apiContext = await pwRequest.newContext({ baseURL: API_URL });
    const regRes = await apiContext.post('/api/v1/auth/player/register', {
      data: { username: `rcuser${uniqueId}`, email, password, tenant_id: tenantId }
    });
    expect(regRes.ok()).toBeTruthy();
    const playerData = await regRes.json();
    const playerId = playerData.player_id || playerData.id;

    // Login for Token
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: tenantId }
    });
    expect(loginRes.ok()).toBeTruthy();
    const loginData = await loginRes.json();
    const playerToken = loginData.access_token;

    // Verify KYC
    const adminLoginRes = await apiContext.post('/api/v1/auth/login', {
      data: { email: 'admin@casino.com', password: 'Admin123!' }
    });
    expect(adminLoginRes.ok()).toBeTruthy();
    const adminToken = (await adminLoginRes.json()).access_token;
    
    const kycRes = await apiContext.post(`/api/v1/kyc/documents/${playerId}/review`, {
      headers: { 'Authorization': `Bearer ${adminToken}` },
      data: { status: 'approved' }
    });
    expect(kycRes.ok()).toBeTruthy();

    // === DEPOSIT ===
    // Login UI
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    
    // Explicit wait for navigation
    // It might go to home then wallet or just wallet.
    // We check if url contains neither login nor initial url
    await expect.poll(() => page.url(), { timeout: 15000 }).not.toContain('/login');
    
    // Force nav if not there
    if (!page.url().includes('/wallet')) {
        await page.goto(`${PLAYER_APP_URL}/wallet`);
    }
    await expect(page).toHaveURL(/\/wallet/);
    
    // Check Balance
    let balance = await getPlayerBalance(apiContext, playerToken);
    const initialAvailable = balance.available_real || 0;

    // We intercept the API call to capture the 'url' from response body directly
    // This avoids relying on UI redirect which might be blocked by headless/browser context or timing
    let depositTxId;
    
    // Setup listener before action
    const depResponsePromise = page.waitForResponse(resp => 
        resp.url().includes('/api/v1/payments/adyen/checkout/session') && resp.status() === 200
    );

    await page.click('button:has-text("Adyen (All Methods)")');
    await page.fill('input[placeholder="Min $10.00"]', '100');
    await page.click('button:has-text("Pay with Adyen")');
    
    const depResponse = await depResponsePromise;
    const depJson = await depResponse.json();
    // depJson = { url: "..." }
    const redirectUrl = depJson.url;
    // Extract ID from URL
    const urlObj = new URL(redirectUrl);
    depositTxId = urlObj.searchParams.get('tx_id');
    expect(depositTxId, "Deposit TX ID not found in API response").toBeTruthy();

    // Simulate Webhook
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: depositTxId, success: true }
    });

    // Verify Balance
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return bal.available_real;
    }, { timeout: 10000 }).toBe(initialAvailable + 100);

    // === WITHDRAW ===
    await page.reload();
    // Robust Tab Click
    const tab = page.locator('button:has-text("Withdraw")');
    if (await tab.count() > 0) await tab.click();
    
    await expect(page.locator('text=Bank Account Details')).toBeVisible();

    // Fill Form
    await page.locator('input[type="number"]').first().fill('50');
    // Generic Inputs
    const inputs = page.locator('input[type="text"]');
    await inputs.nth(0).fill('Smoke User'); 
    await inputs.nth(1).fill('123456');
    await inputs.nth(2).fill('001');
    await inputs.nth(3).fill('ABC');
    if (await inputs.count() > 4) await inputs.nth(4).fill('US');
    if (await inputs.count() > 5) await inputs.nth(5).fill('USD');

    await page.click('button:has-text("Request Withdrawal")');
    // Wait for success toast/text
    await expect(page.locator('text=Withdrawal submitted')).toBeVisible();

    // Verify Invariant (Held 50)
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, { timeout: 10000 }).toEqual({ avail: initialAvailable + 50, held: 50 });

    // Get Withdrawal TX
    const txRes = await apiContext.get(`/api/v1/payouts/player/${playerId}/history`);
    const txData = await txRes.json();
    const withdrawTxId = txData.payouts[0]._id;

    // === ADMIN PAYOUT ===
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.goto(`${ADMIN_APP_URL}/login`);
    if (adminPage.url().includes('404')) await adminPage.goto(`${ADMIN_APP_URL}/admin/login`);
    
    await adminPage.fill('input[name="email"]', 'admin@casino.com');
    await adminPage.fill('input[name="password"]', 'Admin123!');
    await adminPage.click('button[type="submit"]');
    await expect(adminPage).toHaveURL(/\/admin\/dashboard/);

    await adminPage.click('a[href="/admin/finance/withdrawals"]');
    
    const row = adminPage.locator('tr').filter({ hasText: `rcuser${uniqueId}` }).first();
    await expect(row).toBeVisible({ timeout: 15000 });

    if (await row.locator('button:has-text("Approve")').count() > 0) {
        await row.locator('button:has-text("Approve")').click();
        await expect(row).toContainText('Approved');
    }

    await row.locator('button:has-text("Retry")').click();
    await expect(row).toContainText('Payout Pending', { timeout: 15000 });

    // Webhook
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: withdrawTxId, success: true, type: "payout" }
    });

    // === FINAL VERIFY ===
    // Backend Status
    await expect.poll(async () => {
        const res = await apiContext.get(`/api/v1/payouts/status/${withdrawTxId}`);
        return (await res.json()).status;
    }, { timeout: 15000 }).toBe('paid');

    // Ledger Invariant
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, { timeout: 10000 }).toEqual({ avail: initialAvailable + 50, held: 0 });

    console.log('RC Smoke Test Passed');
  });
});

async function getPlayerBalance(apiContext, token) {
    const res = await apiContext.get('/api/v1/player/wallet/balance', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    expect(res.ok()).toBeTruthy();
    return await res.json();
}
