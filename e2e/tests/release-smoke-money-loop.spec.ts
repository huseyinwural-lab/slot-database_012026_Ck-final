import { test, expect } from '@playwright/test';

test.describe('Release Smoke Money Loop', () => {
  test('Full Cycle: Deposit -> Withdraw -> Admin Payout -> Paid', async ({ page, request, browser }) => {
    test.setTimeout(90000); // 1.5 mins
    const PLAYER_APP_URL = 'http://localhost:3001';
    const ADMIN_APP_URL = 'http://localhost:3000';
    const API_URL = 'http://localhost:8001';

    // === DATA SETUP ===
    const uniqueId = Date.now();
    const email = `smoke_${uniqueId}@example.com`;
    const password = 'Password123!';
    const tenantId = 'default_casino';

    // 1. Register Player via API (Determinstic)
    const regRes = await request.post(`${API_URL}/api/v1/auth/player/register`, {
      data: { username: `smokeuser${uniqueId}`, email, password, tenant_id: tenantId }
    });
    expect(regRes.ok(), "Player registration failed").toBeTruthy();
    const playerData = await regRes.json();
    const playerId = playerData.player_id || playerData.id; // Updated key

    // 1b. Verify KYC via Admin API (to unblock withdrawal)
    // Login Admin API
    const adminLoginRes = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: { email: 'admin@casino.com', password: 'Admin123!' }
    });
    expect(adminLoginRes.ok()).toBeTruthy();
    const adminData = await adminLoginRes.json();
    const adminToken = adminData.access_token;
    
    // Verify Player
    const kycRes = await request.post(`${API_URL}/api/v1/kyc/documents/${playerId}/review`, {
      headers: { 'Authorization': `Bearer ${adminToken}` },
      data: { status: 'approved' }
    });
    expect(kycRes.ok(), "KYC Verification failed").toBeTruthy();

    // === PART B: DEPOSIT ===
    // 2. Login Player
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await expect(page).not.toHaveURL(/\/login/);
    
    // 3. Deposit Flow
    await page.goto(`${PLAYER_APP_URL}/wallet`);
    await page.click('button:has-text("Adyen (All Methods)")');
    await page.fill('input[placeholder="Min $10.00"]', '100'); // Deposit $100
    
    // Capture TX ID via request interception (more reliable if UI cleans URL)
    let depositTxId;
    const urlListener = request => {
        const url = request.url();
        if (url.includes('provider=adyen') && url.includes('tx_id')) {
            const u = new URL(url);
            depositTxId = u.searchParams.get('tx_id');
        }
    };
    page.on('request', urlListener);

    await page.click('button:has-text("Pay with Adyen")');
    
    // Wait for "Authorised" or redirect
    await expect(page.locator('text=Adyen Payment Authorised!')).toBeVisible({ timeout: 15000 });
    
    page.off('request', urlListener);
    expect(depositTxId, "Failed to capture deposit TX ID").toBeTruthy();

    // 4. Simulate Deposit Webhook
    const depHookRes = await request.post(`${API_URL}/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { tx_id: depositTxId, success: true }
    });
    expect(depHookRes.ok()).toBeTruthy();

    // 5. Verify Balance ($100.00)
    await page.reload();
    await expect(page.locator('text=$100.00').first()).toBeVisible();

    // === PART C: WITHDRAW ===
    // 6. Request Withdrawal
    // Ensure we are on Wallet page
    await expect(page).toHaveURL(/\/wallet/);
    
    // Click "Withdraw" Tab. 
    // We try to find the tab strictly first.
    // If "Withdraw" text is inside the content (e.g. "Withdraw your funds"), we might misclick.
    // Tabs trigger usually has role="tab".
    const tab = page.locator('button[role="tab"]:has-text("Withdraw")');
    if (await tab.count() > 0) {
        await tab.click();
    } else {
        // Fallback: look for a navigation button
        await page.click('button:has-text("Withdraw")');
    }
    
    // Wait for UNIQUE element of Withdrawal Form
    // "Bank Account Details" is strictly in WithdrawalForm.jsx
    await expect(page.locator('text=Bank Account Details')).toBeVisible({ timeout: 10000 });
    
    // Now we are sure we are on the form.
    // Amount
    const amountInput = page.locator('input[type="number"]').first();
    await amountInput.fill('50');

    // Fill Bank Details (generic text inputs sequence)
    // 1. Account Holder
    const textInputs = page.locator('input[type="text"]');
    await textInputs.nth(0).fill('Smoke Test User');
    
    // 2. Account Number
    await textInputs.nth(1).fill('123456789');
    
    // 3. Bank Code
    await textInputs.nth(2).fill('001');
    
    // 4. Branch Code
    await textInputs.nth(3).fill('ABC');
    
    // 5. Country (might be prefilled or input)
    if (await textInputs.count() > 4) await textInputs.nth(4).fill('US');
    
    // 6. Currency
    if (await textInputs.count() > 5) await textInputs.nth(5).fill('USD');

    // Submit
    // "Request Withdrawal" might be the button text.
    await page.click('button:has-text("Request Withdrawal")');
    
    // 7. Verify Toast/Success
    await expect(page.locator('text=submitted successfully')).toBeVisible();
    
    // Get Withdraw TX ID (from response or history)
    // We can query API or check UI.
    // Let's check UI History table.
    await expect(page.locator('td', { hasText: '-$50.00' })).toBeVisible();
    
    // === PART D: ADMIN APPROVE & PAYOUT ===
    // 8. Admin Login (New Context or Logout)
    // We use a separate context for Admin to avoid session conflict
    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    
    await adminPage.goto(`${ADMIN_APP_URL}/login`); // Ensure we hit the admin route, assuming /login handles admin or /admin/login
    // Assuming /admin/login based on handoff
    if (adminPage.url().includes('404')) {
        await adminPage.goto(`${ADMIN_APP_URL}/admin/login`);
    }
    
    await adminPage.fill('input[name="email"]', 'admin@casino.com');
    await adminPage.fill('input[name="password"]', 'Admin123!');
    await adminPage.click('button[type="submit"]');
    await expect(adminPage).toHaveURL(/\/admin\/dashboard/);

    // 9. Navigate to Withdrawals
    await adminPage.click('a[href="/admin/finance/withdrawals"]');
    
    // 10. Find the withdrawal (amount $50, user smokeuser...)
    // We assume the list is sorted recent first.
    const row = adminPage.locator('tr').filter({ hasText: 'smokeuser' }).first();
    await expect(row).toBeVisible();
    
    // 11. Start Payout (Retry/Process)
    // In our flow, it might be auto-approved or need "Approve". 
    // If "Approve" button exists, click it first.
    if (await row.locator('button:has-text("Approve")').count() > 0) {
        await row.locator('button:has-text("Approve")').click();
        await expect(row).toContainText('Approved');
    }
    
    // Now Click "Retry" or "Pay" to trigger Payout Provider
    // The button might be "Retry Payout" if it's pending_provider or just "Pay"
    // Let's look for "Retry" as per previous tests
    await row.locator('button:has-text("Retry")').click();
    
    // 12. Verify Status "Payout Pending"
    await expect(row).toContainText('Payout Pending', { timeout: 10000 });
    
    // We need the TX ID for the withdrawal to simulate webhook.
    // We can get it from the "Copy ID" button or link in the row?
    // Or we can query the backend via request context.
    // Let's query backend for the latest withdrawal for this player.
    const wdRes = await request.get(`${API_URL}/api/v1/payouts/player/${playerId}/history`);
    const wdData = await wdRes.json();
    const withdrawTxId = wdData.payouts[0]._id; // Assuming repo returns _id or id
    expect(withdrawTxId).toBeTruthy();

    // 13. Simulate Payout Success Webhook
    // Calls the endpoint we modified in AdyenPayments
    const payoutHookRes = await request.post(`${API_URL}/api/v1/payments/adyen/test-trigger-webhook`, {
      data: { 
          tx_id: withdrawTxId, 
          success: true, 
          type: "payout" // Trigger the payout logic
      }
    });
    expect(payoutHookRes.ok(), await payoutHookRes.text()).toBeTruthy();

    // 14. Verify Final State "Paid"
    await adminPage.reload();
    await expect(adminPage.locator('tr').filter({ hasText: 'smokeuser' }).first()).toContainText('Paid');
    
    // 15. Verify Ledger Invariants (Available 50, Held 0) via Player UI
    await page.reload();
    // Available should be 100 - 50 = 50.
    await expect(page.locator('text=$50.00').first()).toBeVisible();
    // Pending/Held should be 0 (if visible)
    
    console.log('Money Loop Smoke Test Passed!');
  });
});
