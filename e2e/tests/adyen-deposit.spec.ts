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

    // 5. Submit
    // Since backend returns a mock URL that redirects back to /wallet, we just click and wait.
    await page.click('button:has-text("Pay with Adyen")');

    // 6. Wait for success params
    await page.waitForURL(/wallet\?provider=adyen.*resultCode=Authorised/);
    
    // Check UI message
    await expect(page.locator('text=Adyen Payment Authorised!')).toBeVisible();

    // 7. Extract tx_id from URL
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);
    const url = new URL(currentUrl);
    const txId = url.searchParams.get('tx_id');
    expect(txId).toBeTruthy();

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
