import { test, expect } from '@playwright/test';

test.describe('Stripe Deposit Flow (Simulated)', () => {
  test('User can initiate deposit and see balance update after simulated webhook', async ({ page, request }) => {
    test.setTimeout(120000);

    // 1. Go to Login
    await page.goto('/login');
    const uniqueId = Date.now();
    const email = `stripe_e2e_${uniqueId}@example.com`;
    
    // 2. Go to Register (Look for ANY link that goes to register)
    await page.click('a[href="/register"]'); 
    
    // 3. Register Form
    // Try to find inputs by placeholder if name fails, but name should work.
    // Debugging: Screenshot might show if we are actually on register page.
    await expect(page).toHaveURL(/\/register/);
    
    // Sometimes the input names are slightly different or nested
    // Let's use getByPlaceholder if possible or generic
    await page.fill('input[type="text"]', `user${uniqueId}`); // Username usually first
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'password123');
    
    await page.click('button[type="submit"]');

    // 4. Login
    await expect(page).toHaveURL(/\/login/);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL(/\/wallet/, { timeout: 20000 });

    // 5. Initiate Deposit
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
    // Assuming deposit tab is active by default
    await page.fill('input[type="number"]', '50');
    
    const payBtn = page.locator('button:has-text("Pay with Stripe")');
    await expect(payBtn).toBeEnabled();
    await payBtn.click();

    // 6. Verify Polling State
    await expect(page).toHaveURL(/session_id=cs_/, { timeout: 10000 });
    await expect(page.locator('text=Verifying payment...')).toBeVisible();

    // 7. Trigger Webhook Simulation
    expect(sessionId).toBeTruthy();

    const webhookRes = await request.post('http://localhost:8001/api/v1/payments/stripe/test-trigger-webhook', {
        data: {
            type: 'checkout.session.completed',
            session_id: sessionId
        }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 8. Verify Success UI
    await expect(page.locator('text=Payment Successful!')).toBeVisible({ timeout: 20000 });
    
    // 9. Verify Balance Update
    await expect(page.locator('text=$50.00')).toBeVisible();
  });
});
