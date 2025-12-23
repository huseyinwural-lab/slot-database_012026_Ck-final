import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    test.setTimeout(60000);

    // Direct navigation to register
    await page.goto('/register');
    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    
    // Register
    await page.waitForSelector('form'); // Wait for form to ensure hydration
    // Use generic selectors if named ones fail, but assuming standard layout
    await page.fill('input[type="text"]', `user${uniqueId}`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Login
    await expect(page).toHaveURL(/\/login/);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/wallet/, { timeout: 20000 });

    // Initiate Deposit
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
    await page.click('text=Deposit');
    await page.fill('input[type="number"]', '50');
    
    const payBtn = page.locator('button:has-text("Pay with Stripe")');
    await expect(payBtn).toBeEnabled();
    await payBtn.click();

    // Verify Polling State
    await expect(page).toHaveURL(/session_id=cs_/, { timeout: 10000 });
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // Trigger Webhook Simulation
    expect(sessionId).toBeTruthy();

    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // Verify Success UI
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 20000 });
    
    // Verify Balance Update
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
