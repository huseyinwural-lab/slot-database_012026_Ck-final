import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    test.setTimeout(60000);

    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    const password = 'password123';

    // 1. Register User via API (since frontend register page is missing)
    const registerRes = await request.post('http://localhost:8001/api/v1/auth/player/register', {
        data: {
            username: `user${uniqueId}`,
            email: email,
            password: password,
            tenant_id: 'default_casino'
        }
    });
    expect(registerRes.ok()).toBeTruthy();

    // 2. Login via Frontend
    await page.goto('/login');
    await page.waitForSelector('input[name="email"]');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');

    // 3. Verify Landing on Wallet
    await expect(page).toHaveURL(/\/wallet/, { timeout: 20000 });

    // 4. Initiate Deposit
    let sessionId = '';
    await page.route('**/api/v1/payments/stripe/checkout/session', async route => {
      const response = await route.fetch();
      const json = await response.json();
      sessionId = json.session_id;
      
      await route.fulfill({
        json: {
            ...json,
            url: `${page.url()}?session_id=${sessionId}&status=success`
        }
      });
    });

    // Ensure we are on wallet page and deposit tab is active
    // If not active by default, click it. Assuming it is.
    await page.click('text=Deposit');
    await page.fill('input[type="number"]', '50');
    
    const payBtn = page.locator('button:has-text("Pay with Stripe")');
    await expect(payBtn).toBeEnabled();
    await payBtn.click();

    // 5. Verify Polling State
    await expect(page).toHaveURL(/session_id=cs_/, { timeout: 10000 });
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 6. Trigger Webhook Simulation
    expect(sessionId).toBeTruthy();

    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 7. Verify Success UI
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 20000 });
    
    // 8. Verify Balance Update
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
