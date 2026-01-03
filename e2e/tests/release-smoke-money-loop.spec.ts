import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Release Smoke Money Loop (Deterministic)', () => {
  test.setTimeout(180000); 

  test('Full Cycle: Deposit -> Withdraw -> Admin Payout -> Paid', async ({ page, browser }) => {
    const PLAYER_APP_URL = process.env.PLAYER_APP_URL || 'http://localhost:3001';
    const ADMIN_APP_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';
    const API_URL = process.env.E2E_API_BASE || 'http://localhost:8001';

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
    expect(regRes.ok(), "Registration failed").toBeTruthy();
    const playerData = await regRes.json();
    const playerId = playerData.user?.id || playerData.id || playerData.player_id;
    if (!playerId) {
      throw new Error(`register response missing player id: ${JSON.stringify(playerData)}`);
    }

    // Login for Token
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password, tenant_id: tenantId }
    });
    expect(loginRes.ok(), "Player login failed").toBeTruthy();
    const loginData = await loginRes.json();
    const playerToken = loginData.access_token;

    // Verify KYC
    const adminLoginRes = await apiContext.post('/api/v1/auth/login', {
      data: { email: 'admin@casino.com', password: 'Admin123!' }
    });
    expect(adminLoginRes.ok(), "Admin API login failed").toBeTruthy();
    const adminToken = (await adminLoginRes.json()).access_token;
    
    const kycRes = await apiContext.post(`/api/v1/kyc/documents/${playerId}/review`, {
      headers: { 'Authorization': `Bearer ${adminToken}` },
      data: { status: 'approved' }
    });
    expect(kycRes.ok(), "KYC approval failed").toBeTruthy();

    // === DEPOSIT ===
    // Login UI
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    
    // Explicit wait for navigation
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
    let depositTxId;
    
    // Trigger Deposit (Adyen)
    await page.click('button:has-text("Adyen (All Methods)")');
    await page.fill('input[placeholder="Min $10.00"]', '100');
    await page.click('button:has-text("Pay with Adyen")');
    
    // Wait for redirect to happen and capture URL
    // This avoids "Protocol error" when trying to read response body of a request 
    // that triggered an immediate navigation.
    await expect.poll(() => page.url(), { timeout: 15000 }).toContain('tx_id=');
    
    const currentUrl = new URL(page.url());
    depositTxId = currentUrl.searchParams.get('tx_id');
    expect(depositTxId, "Deposit TX ID not found in Page URL").toBeTruthy();

    // Simulate Webhook (Backend state change)
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: depositTxId, success: true }
    });

    // Verify Balance via API Polling
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return bal.available_real;
    }, { timeout: 15000, message: "Balance did not update after deposit" }).toBe(initialAvailable + 100);

    // === WITHDRAW ===
    await page.reload(); // Robust Tab Click
    const tab = page.locator('button:has-text("Withdraw")');
    if (await tab.count() > 0) await tab.click();
    
    await expect(page.locator('text=Bank Account Details')).toBeVisible({ timeout: 10000 });

    // Fill Form with Robust Selectors
    await page.fill('input[name="amount"]', '50');
    await page.fill('input[name="accountHolderName"]', 'Smoke User');
    await page.fill('input[name="accountNumber"]', '123456789');
    await page.fill('input[name="bankCode"]', '021000021');
    await page.fill('input[name="branchCode"]', '001');
    await page.fill('input[name="countryCode"]', 'US');
    await page.fill('input[name="currencyCode"]', 'USD');

    // Click and Wait for Success Transition
    await page.click('button:has-text("Request Withdrawal")');
    
    // Upon success, the form is replaced by the WithdrawalStatus component
    await expect(page.locator('text=Withdrawal Status')).toBeVisible({ timeout: 15000 });

    // Verify Invariant (Held 50) via API Polling
    // This implicitly confirms the withdrawal was created successfully
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, { timeout: 15000, message: "Balance did not update after withdrawal request" }).toEqual({ avail: initialAvailable + 50, held: 50 });

    // Get Withdrawal TX ID for further tracking
    const txRes = await apiContext.get(`/api/v1/payouts/player/${playerId}/history`);
    const txData = await txRes.json();
    console.log('payout_history', JSON.stringify(txData));
    const withdrawTxId = txData.payouts?.[0]?._id;
    if (!withdrawTxId) {
      throw new Error(`No withdrawal in payout history for playerId=${playerId}. body=${JSON.stringify(txData)}`);
    }
    console.log(`Tracking Withdrawal TX: ${withdrawTxId}`);

    // === ADMIN PAYOUT ===
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    await adminPage.goto(`${ADMIN_APP_URL}/login`);
    if (adminPage.url().includes('404')) await adminPage.goto(`${ADMIN_APP_URL}/admin/login`);
    
    // Login with robust selectors (id based)
    await adminPage.fill('#email', 'admin@casino.com');
    await adminPage.fill('#password', 'Admin123!');
    await adminPage.click('button[type="submit"]');
    // Login redirects to /, which is the Dashboard
    await expect(adminPage).toHaveURL(`${ADMIN_APP_URL}/`, { timeout: 15000 });

    // Navigate to Withdrawals directly
    await adminPage.goto(`${ADMIN_APP_URL}/finance/withdrawals`);
    await expect(adminPage).toHaveURL(/\/finance\/withdrawals/, { timeout: 15000 });
    
    // Find row by Player ID (not username, as table shows ID)
    const row = adminPage.locator('tr').filter({ hasText: playerId }).first();
    await expect(row).toBeVisible({ timeout: 15000 });

    // 1. Approve (if needed)
    if (await row.locator('button:has-text("Approve")').count() > 0) {
        await row.locator('button:has-text("Approve")').click();
        
        // Handle Approval Modal
        await expect(adminPage.locator('text=Approve Withdrawal')).toBeVisible();
        await adminPage.fill('textarea', 'Smoke Test Approval');
        await adminPage.click('button:has-text("Confirm")');
        
        // Poll API for 'approved' status
        await expect.poll(async () => {
            const res = await apiContext.get(`/api/v1/payouts/status/${withdrawTxId}`);
            return (await res.json()).status;
        }, { timeout: 15000, message: "Status did not become 'approved'" }).toBe('approved');
    }

    // 2. Start/Retry Payout
    // Button text depends on state
    const payoutBtn = row.locator('button:has-text("Start Payout"), button:has-text("Retry Payout")');
    await expect(payoutBtn).toBeVisible({ timeout: 10000 });
    await payoutBtn.click();
    
    // Poll API for 'payout_submitted' or 'paid' (if instant)
    await expect.poll(async () => {
        const res = await apiContext.get(`/api/v1/payouts/status/${withdrawTxId}`);
        const st = (await res.json()).status;
        return st;
    }, { timeout: 15000, message: "Status did not become 'payout_submitted' or 'paid'" }).toMatch(/payout_(submitted|pending)|paid/);

    // Webhook - Simulate Adyen calling us back
    await apiContext.post(`/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: withdrawTxId, success: true, type: "payout" }
    });

    // === FINAL VERIFY ===
    // Backend Status -> 'paid' or 'completed'
    await expect.poll(async () => {
        const res = await apiContext.get(`/api/v1/payouts/status/${withdrawTxId}`);
        const st = (await res.json()).status;
        return st;
    }, { timeout: 15000, message: "Final status is not 'paid' or 'completed'" }).toMatch(/paid|completed/);

    // Ledger Invariant -> Held should be 0
    await expect.poll(async () => {
        const bal = await getPlayerBalance(apiContext, playerToken);
        return { avail: bal.available_real, held: bal.held_real };
    }, { timeout: 15000, message: "Ledger did not settle (Held != 0)" }).toEqual({ avail: initialAvailable + 50, held: 0 });

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
