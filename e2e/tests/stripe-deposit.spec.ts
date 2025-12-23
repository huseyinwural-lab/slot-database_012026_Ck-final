import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    // Increase timeout
    test.setTimeout(120000);

    // 1. Login
    await page.goto('/login');
    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    
    // Check if register link exists
    if (await page.isVisible('a[href="/register"]')) {
        await page.click('a[href="/register"]');
    } else {
        await page.goto('/register');
    }

    // Wait for inputs
    await page.waitForSelector('input[name="username"]', { timeout: 10000 });
    await page.fill('input[name="username"]', `user${uniqueId}`);
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    
    // Handle potential different button texts
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    // 2. Login
    await expect(page).toHaveURL(/\/login/);
    await page.waitForSelector('input[name="email"]');
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/wallet/, { timeout: 15000 });

    // 3. Initiate Deposit
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

    await page.click('text=Deposit');
    await page.waitForSelector('input[placeholder="Min $10.00"]');
    await page.fill('input[placeholder="Min $10.00"]', '50');
    
    // Wait for "Pay with Stripe" button to be enabled
    const payBtn = page.locator('button:has-text("Pay with Stripe")');
    await expect(payBtn).toBeEnabled();
    await payBtn.click();

    // 4. Verify Polling State
    await expect(page).toHaveURL(/session_id=cs_/, { timeout: 10000 });
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 5. Trigger Webhook Simulation
    // Need to trigger the backend simulation
    // Ensure sessionId was captured
    expect(sessionId).toBeTruthy();

    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 6. Verify Success UI
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 20000 });
    
    // 7. Verify Balance Update
    // Initial balance 0, deposited 50.
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
