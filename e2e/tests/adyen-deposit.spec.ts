import { test, expect } from '@playwright/test';

test.describe('Adyen Deposit Flow', () => {
  test('should successfully deposit via Adyen (Mock)', async ({ page, request }) => {
    test.setTimeout(60000);
    const PLAYER_APP_URL = 'http://localhost:3001';
    const API_URL = 'http://localhost:8001';

    const uniqueId = Date.now();
    const email = `adyen_test_${uniqueId}@example.com`;
    const password = 'Password123!';

    // 1. Register
    const regRes = await request.post(`${API_URL}/api/v1/auth/player/register`, {
      data: {
        username: `adyenuser${uniqueId}`,
        email,
        password,
        tenant_id: 'default_casino'
      }
    });
    expect(regRes.ok()).toBeTruthy();

    // 2. Login
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    
    // Wait for login to complete and land on wallet or dashboard
    await expect(page).not.toHaveURL(/\/login/);
    await page.goto(`${PLAYER_APP_URL}/wallet`);

    // 3. Select Adyen
    // Wait for the button to appear
    await page.waitForSelector('button:has-text("Adyen (All Methods)")');
    await page.click('button:has-text("Adyen (All Methods)")');

    // 4. Enter Amount
    await page.fill('input[placeholder="Min $10.00"]', '55');

    // 5. Submit & Intercept Response
    const [response] = await Promise.all([
      page.waitForResponse(res => res.url().includes('/api/v1/payments/adyen/checkout/session') && res.status() === 200),
      page.click('button:has-text("Pay with Adyen")')
    ]);

    const json = await response.json();
    const redirectUrl = new URL(json.url);
    const txId = redirectUrl.searchParams.get('tx_id');
    expect(txId).toBeTruthy();

    // 6. Wait for success UI (URL might be cleared by then)
    await page.waitForURL(/wallet/); // Just wait for any wallet url, or specific success state
    await expect(page.locator('text=Adyen Payment Authorised!')).toBeVisible();

    // 7. (Skip URL extraction since we have txId)
    
    // 8. Simulate Webhook
    // Note: The UI says "Authorised" but the balance doesn't update until webhook.
    const webhookRes = await request.post(`${API_URL}/api/v1/payments/adyen/test-trigger-webhook`, {
      data: {
        tx_id: txId,
        success: true
      }
    });
    expect(webhookRes.ok()).toBeTruthy();

    // 9. Verify Balance Update
    await page.click('button[title="Refresh Data"]'); // Click refresh button
    // Or reload page
    // await page.reload();
    
    // Expect $55.00
    await expect(page.locator('text=$55.00').first()).toBeVisible();

    // 10. Verify History
    await expect(page.locator('td', { hasText: '+$55.00' })).toBeVisible();
  });
});
