import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    // 1. Login
    await page.goto('/login');
    // Register if needed, or assume clean state. Since tests run in parallel or isolation, 
    // it's safer to register a unique user.
    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    
    await page.goto('/register');
    await page.fill('input[name="username"]', `user${uniqueId}`);
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/login/);
    
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/wallet/);

    // 2. Initiate Deposit
    // Intercept the session creation to capture the session_id
    let sessionId = '';
    await page.route('**/api/v1/payments/stripe/checkout/session', async route => {
      const response = await route.fetch();
      const json = await response.json();
      sessionId = json.session_id;
      
      // Mock the redirect to just reload the page with success params
      // This simulates returning from Stripe
      await route.fulfill({
        json: {
            ...json,
            url: `${page.url()}?session_id=${sessionId}&status=success`
        }
      });
    });

    await page.click('text=Deposit');
    // Ensure input is visible
    await expect(page.locator('input[placeholder="Min $10.00"]')).toBeVisible();
    await page.fill('input[placeholder="Min $10.00"]', '50');
    await page.click('button:has-text("Pay with Stripe")');

    // 3. Verify Polling State
    await expect(page).toHaveURL(/session_id=cs_/);
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 4. Trigger Webhook Simulation
    // Need to trigger the backend simulation
    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 5. Verify Success UI
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 15000 });
    
    // 6. Verify Balance Update
    // Initial balance 0, deposited 50.
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
