import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Release Smoke Money Loop (Deterministic)', () => {
  test.setTimeout(90000); // 1.5 minutes total

  test('Full Cycle: Deposit -> Withdraw -> Admin Payout -> Paid', async ({ page, browser }) => {
    const PLAYER_APP_URL = 'http://localhost:3001';
    const ADMIN_APP_URL = 'http://localhost:3000';
    const API_URL = 'http://localhost:8001';

    // === DATA SETUP ===
    const uniqueId = Date.now();
    const email = `rc_${uniqueId}@example.com`;
    const password = 'Password123!';
    const tenantId = 'default_casino';

    // 1. Register Player via API
    const apiContext = await pwRequest.newContext({ baseURL: API_URL });
    const regRes = await apiContext.post('/api/v1/auth/player/register', {
      data: { username: `rcuser${uniqueId}`, email, password, tenant_id: tenantId }
    });
    expect(regRes.ok(), `Player registration failed: ${regRes.status()}`).toBeTruthy();
    const playerData = await regRes.json();
    const playerId = playerData.player_id || playerData.id;

    // Login for Token (Player)
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: tenantId }
    });
    expect(loginRes.ok(), "Login failed").toBeTruthy();
    const loginData = await loginRes.json();
    const playerToken = loginData.access_token;

    // Verify KYC via Admin API (Unblock Withdrawal)
    const adminLoginRes = await apiContext.post('/api/v1/auth/login', {
      data: { email: 'admin@casino.com', password: 'Admin123!' }
    });
    expect(adminLoginRes.ok(), "Admin login failed").toBeTruthy();
    const adminData = await adminLoginRes.json();
    const adminToken = adminData.access_token;
    
    const kycRes = await apiContext.post(`/api/v1/kyc/documents/${playerId}/review`, {
      headers: { 'Authorization': `Bearer ${adminToken}` },
      data: { status: 'approved' }
    });
    expect(kycRes.ok(), "KYC Verification failed").toBeTruthy();

    // === PART B: DEPOSIT ===
    // 2. Login Player UI
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/wallet|dashboard/); // Wait for redirect
    
    // 3. Deposit Flow
    await page.goto(`${PLAYER_APP_URL}/wallet`);
    
    // Check initial balance via API (Poll invariant)
    let balance = await getPlayerBalance(apiContext, playerToken);
    const initialAvailable = balance.available_real || 0;

    // Trigger Deposit (Adyen)
    // We intercept the request to get the TX ID without relying on UI redirect parsing if flaky
    let depositTxId;
    const [depReq] = await Promise.all([
        page.waitForRequest(req => req.url().includes('/api/v1/payments/adyen/checkout/session') && req.method() === 'POST'),
        page.click('button:has-text("Adyen (All Methods)")').then(() => 
            page.fill('input[placeholder="Min $10.00"]', '100').then(() => 
                page.click('button:has-text("Pay with Adyen")')
            )
        )
    ]);
    
    // Wait for response to get Redirect URL which usually has TX ID or we can query
    // Actually, `checkout/session` response returns `{url: ...}`.
    const depRes = await depReq.response();
    const depJson = await depRes.json();
    // The URL is like `.../wallet?provider=adyen&tx_id=...`
    const redirectUrl = depJson.url;
    const urlObj = new URL(redirectUrl);
    depositTxId = urlObj.searchParams.get('tx_id');
    expect(depositTxId, "Deposit TX ID not found").toBeTruthy();

    // 4. Simulate Deposit Webhook (Adyen)
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: depositTxId, success: true }
    });

    // 5. Verify Balance Update (Invariant Poll)
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return bal.available_real;
    }, {
        message: 'Balance did not update after deposit',
        timeout: 10000
    }).toBe(initialAvailable + 100);

    // === PART C: WITHDRAW ===
    // 6. Request Withdrawal
    await page.reload();
    // Use robust selection for Tabs
    const tab = page.locator('button[role="tab"]:has-text("Withdraw")');
    if (await tab.count() > 0) {
        await tab.click();
    } else {
        await page.click('button:has-text("Withdraw")');
    }
    await expect(page.locator('text=Bank Account Details')).toBeVisible();

    // Fill Form
    await page.locator('input[type="number"]').first().fill('50');
    // Generic inputs filling
    const inputs = page.locator('input[type="text"]');
    // Account Holder
    await inputs.nth(0).fill('RC Smoke User'); 
    // Account Number
    await inputs.nth(1).fill('123456789');
    // Bank Code
    await inputs.nth(2).fill('001');
    // Branch Code
    await inputs.nth(3).fill('ABC');
    // Country
    if (await inputs.count() > 4) await inputs.nth(4).fill('US');
    // Currency
    if (await inputs.count() > 5) await inputs.nth(5).fill('USD');

    await page.click('button:has-text("Request Withdrawal")');
    await expect(page.locator('text=Withdrawal submitted')).toBeVisible();

    // Verify Held Balance (Invariant Poll)
    // Available should be 50, Held 50
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, {
        message: 'Held balance did not update after withdrawal request',
        timeout: 10000
    }).toEqual({ avail: initialAvailable + 50, held: 50 });

    // Get Withdrawal TX ID
    const txRes = await apiContext.get(`/api/v1/payouts/player/${playerId}/history`, {
        headers: { 'Authorization': `Bearer ${playerToken}` } // If needed, or use public
    });
    const txData = await txRes.json();
    const withdrawTxId = txData.payouts[0]._id;

    // === PART D: ADMIN PAYOUT ===
    // 7. Admin Action (API-driven for stability in "Smoke" context, or headless UI)
    // We use API to approve and retry payout to avoid Admin UI flakes (tables, filters)
    // But Work Order asks for "Money Loop", implying UI usage.
    // Let's use UI but with robust locators.
    
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.goto(`${ADMIN_APP_URL}/login`);
    // Handle redirect if any
    if (adminPage.url().includes('404')) await adminPage.goto(`${ADMIN_APP_URL}/admin/login`);
    
    await adminPage.fill('input[name="email"]', 'admin@casino.com');
    await adminPage.fill('input[name="password"]', 'Admin123!');
    await adminPage.click('button[type="submit"]');
    await expect(adminPage).toHaveURL(/\/admin\/dashboard/);

    await adminPage.click('a[href="/admin/finance/withdrawals"]');
    
    // Filter or finding row
    const row = adminPage.locator('tr').filter({ hasText: `rcuser${uniqueId}` }).first();
    await expect(row).toBeVisible({ timeout: 15000 });

    // Approve if needed
    if (await row.locator('button:has-text("Approve")').count() > 0) {
        await row.locator('button:has-text("Approve")').click();
        await expect(row).toContainText('Approved');
    }

    // Retry/Pay
    await row.locator('button:has-text("Retry")').click();
    await expect(row).toContainText('Payout Pending', { timeout: 15000 });

    // 8. Simulate Payout Webhook (Adyen)
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: withdrawTxId, success: true, type: "payout" }
    });

    // === PART E: FINAL VERIFICATION (API Polling) ===
    // 9. Verify "Paid" State (Backend)
    await expect.poll(async () => {
        const res = await apiContext.get(`/api/v1/payouts/status/${withdrawTxId}`);
        const json = await res.json();
        return json.status;
    }, {
        message: 'Payout status never became "paid"',
        timeout: 15000
    }).toBe('paid');

    // 10. Verify Ledger Invariant (Held Burned)
    // Available should remain 50, Held should be 0.
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, {
        message: 'Ledger invariant failed: Held balance not burned',
        timeout: 10000
    }).toEqual({ avail: initialAvailable + 50, held: 0 });

    console.log('RC Smoke Test Passed: State + Ledger Invariants Verified');
  });
});

async function getPlayerBalance(apiContext, token) {
    const res = await apiContext.get('/api/v1/player/wallet/balance', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    expect(res.ok()).toBeTruthy();
    return await res.json();
}
