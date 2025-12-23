import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    // 1. Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'testuser@example.com'); // Assuming test user exists or we register
    // To ensure user exists, we might need a register flow or fixture. 
    // For simplicity, let's register a new user for this test.
    const uniqueId = Date.now();
    const email = `stripe_test_${uniqueId}@example.com`;
    
    await page.goto('/register');
    await page.fill('input[name="username"]', `user${uniqueId}`);
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]'); // Adjust selector if needed
    // Wait for redirect to login or auto-login
    await expect(page).toHaveURL(/\/login/);
    
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for wallet page or dashboard
    await expect(page).toHaveURL(/\/wallet/);

    // 2. Initiate Deposit
    // Intercept the session creation to capture the session_id
    let sessionId = '';
    await page.route('**/api/v1/payments/stripe/checkout/session', async route => {
      const response = await route.fetch();
      const json = await response.json();
      sessionId = json.session_id;
      // We do NOT want to redirect to real Stripe, so we fulfill with a dummy URL
      // But the frontend code does: window.location.href = res.data.url
      // We can mock the response to have a url that is just the current page with a query param
      // so it "redirects" back immediately, or just let it redirect and then we navigate back.
      // Better: Mock the response to redirect to a "waiting" page on our app?
      // Actually, let's just let it return the real response (so DB is updated), 
      // but we override the window.location.href behavior in the page context? 
      // Too complex.
      // Let's just mock the response to return a URL that is safe, e.g., the wallet page itself.
      
      await route.fulfill({
        json: {
            ...json,
            url: `${page.url()}?session_id=${sessionId}&status=success` // Simulate immediate return
        }
      });
    });

    await page.click('text=Deposit');
    await page.fill('input[placeholder="Min $10.00"]', '50');
    await page.click('button:has-text("Pay with Stripe")');

    // 3. Verify Polling State
    // The page should reload/redirect to itself with session_id
    await expect(page).toHaveURL(/session_id=cs_/);
    
    // Check that it says "Payment is being processed" or similar (polling)
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 4. Trigger Webhook Simulation
    // Now we simulate the backend receiving the webhook
    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 5. Verify Success UI
    // The polling should pick up the "paid" status
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 15000 });
    
    // 6. Verify Balance Update
    // Initial balance was 0. Deposit 50.
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
