import { test, expect } from '@playwright/test';
import { generateUser } from '../utils/data-gen';

test.describe('Adyen Deposit Flow', () => {
  let user;
  let authToken;

  test.beforeEach(async ({ page, request }) => {
    // 1. Register a new user
    user = generateUser();
    const regRes = await request.post(`${process.env.REACT_APP_BACKEND_URL}/api/v1/auth/register`, {
      data: user
    });
    expect(regRes.ok()).toBeTruthy();

    // 2. Login
    const loginRes = await request.post(`${process.env.REACT_APP_BACKEND_URL}/api/v1/auth/login`, {
      data: { email: user.email, password: user.password }
    });
    expect(loginRes.ok()).toBeTruthy();
    const loginData = await loginRes.json();
    authToken = loginData.access_token;

    // 3. Set localStorage and reload to be logged in
    await page.goto('/');
    await page.evaluate(({ token, user }) => {
      localStorage.setItem('access_token', token);
      localStorage.setItem('player_user', JSON.stringify(user));
    }, { token: authToken, user: user });
  });

  test('should successfully deposit via Adyen (Mock)', async ({ page, request }) => {
    await page.goto('/wallet');
    
    // Check initial balance
    await expect(page.locator('text=$0.00').first()).toBeVisible();

    // 1. Select Adyen
    await page.click('text=Adyen (All Methods)');

    // 2. Enter Amount
    await page.fill('input[placeholder="Min $10.00"]', '50');

    // 3. Submit
    // We expect a redirect. Since it's a mock, it redirects immediately back to /wallet
    // with query params.
    await page.click('button:has-text("Pay with Adyen")');

    // 4. Wait for redirect back to wallet with success params
    // The URL should contain provider=adyen and resultCode=Authorised
    await page.waitForURL(/wallet\?provider=adyen&tx_id=.*&resultCode=Authorised/);
    
    // Check for success message
    await expect(page.locator('text=Adyen Payment Authorised!')).toBeVisible();

    // 5. Extract tx_id from URL
    const url = new URL(page.url());
    const txId = url.searchParams.get('tx_id');
    expect(txId).toBeTruthy();

    // 6. Simulate Webhook (Backend confirmation)
    // In real life, Adyen sends this. In test, we force it.
    const webhookRes = await request.post(`${process.env.REACT_APP_BACKEND_URL}/api/v1/payments/adyen/test-trigger-webhook`, {
      headers: { 'Authorization': `Bearer ${authToken}` }, // Auth not strictly needed for this endpoint but good practice? 
      // Actually test-trigger-webhook is not auth protected in my code? 
      // Let's check. It has "session: AsyncSession". No "Depends(get_current_player)".
      // So it's public (but env guarded).
      data: {
        tx_id: txId,
        success: true
      }
    });
    expect(webhookRes.ok()).toBeTruthy();
    const webhookData = await webhookRes.json();
    expect(webhookData.status).toBe('simulated_success');

    // 7. Verify Balance Update
    // Refresh the page or click refresh button
    await page.reload();
    await expect(page.locator('text=$50.00').first()).toBeVisible();

    // 8. Verify Transaction History
    await expect(page.locator('td', { hasText: '+$50.00' })).toBeVisible();
    await expect(page.locator('span:has-text("completed")')).toBeVisible();
  });
});
