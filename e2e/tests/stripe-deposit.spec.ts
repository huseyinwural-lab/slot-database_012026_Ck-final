import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    test.setTimeout(90000);
    
    const PLAYER_APP_URL = process.env.PLAYER_APP_URL || 'http://localhost:3001';

    // Debug console logs from browser
    page.on('console', msg => console.log(`BROWSER LOG: ${msg.text()}`));
    page.on('pageerror', err => console.log(`BROWSER ERROR: ${err}`));

    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    const password = 'password123';

    // 1. Register via API
    console.log(`Registering user ${email}...`);
    const registerRes = await request.post('http://localhost:8001/api/v1/auth/player/register', {
        data: {
            username: `user${uniqueId}`,
            email: email,
            password: password,
            tenant_id: 'default_casino'
        }
    });
    expect(registerRes.ok()).toBeTruthy();

    // 2. Login via Frontend (Player App)
    console.log('Navigating to login...');
    await page.goto(`${PLAYER_APP_URL}/login`);
    
    // Wait for ANY input to ensure page loaded
    await page.waitForSelector('input', { timeout: 20000 });
    
    console.log('Filling credentials...');
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');

    // 3. Wait for Login Success (Redirect away from login)
    console.log('Waiting for login redirect...');
    await expect(page).not.toHaveURL(/\/login/, { timeout: 20000 });
    
    // Explicitly navigate to wallet to ensure we are there
    console.log('Navigating to wallet...');
    await page.goto(`${PLAYER_APP_URL}/wallet`);
    await expect(page).toHaveURL(new RegExp(`${PLAYER_APP_URL}/wallet`), { timeout: 20000 });

    // 4. Initiate Deposit
    console.log('Initiating deposit...');
    let sessionId = '';
    await page.route('**/api/v1/payments/stripe/checkout/session', async route => {
      console.log('Intercepted checkout session request');
      const response = await route.fetch();
      const json = await response.json();
      sessionId = json.session_id;
      console.log('Captured Session ID:', sessionId);
      
      await route.fulfill({
        json: {
            ...json,
            url: `${PLAYER_APP_URL}/wallet?session_id=${sessionId}&status=success`
        }
      });
    });

    // Ensure we are on wallet page
    // Click Deposit tab if it exists (it might be default)
    const depositTab = page.locator('button:has-text("Deposit")');
    if (await depositTab.isVisible()) {
        await depositTab.click();
    }

    // Wait for input to be visible and editable
    const amountInput = page.locator('input[type="number"]');
    await expect(amountInput).toBeVisible();
    await amountInput.fill('50');
    
    const payBtn = page.locator('button:has-text("Pay with Stripe")');
    await expect(payBtn).toBeEnabled();
    await payBtn.click();

    // 5. Verify Polling State
    console.log('Verifying polling state...');
    await expect(page).toHaveURL(/session_id=cs_/, { timeout: 15000 });
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 6. Trigger Webhook Simulation
    console.log('Triggering webhook simulation...');
    expect(sessionId).toBeTruthy();

    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 7. Verify Success UI
    console.log('Waiting for success message...');
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 20000 });
    
    // 8. Verify Balance Update
    console.log('Verifying balance...');
    // Look for first occurrence or specific container
    // We expect at least one "$50.00"
    await expect(page.locator('text=$50.00').first()).toBeVisible();
  });
});
