import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Casino E2E with Security', () => {
  test.setTimeout(120000);

  test('Full Loop with Signed Webhooks', async ({ page }) => {
    const API_URL = process.env.E2E_API_BASE || 'http://localhost:8001';
    const PLAYER_APP_URL = process.env.PLAYER_APP_URL || 'http://localhost:3001';
    
    // 1. Setup User
    const uniqueId = Date.now();
    const email = `secure_gamer_${uniqueId}@example.com`;
    const apiContext = await pwRequest.newContext({ baseURL: API_URL });
    
    await apiContext.post('/api/v1/auth/player/register', {
      data: { username: `gamer${uniqueId}`, email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    const token = (await loginRes.json()).access_token;
    
    // Deposit 100 (deposit endpoint requires Idempotency-Key)
    await apiContext.post('/api/v1/player/wallet/deposit', {
        headers: { 'Authorization': `Bearer ${token}`, 'Idempotency-Key': `e2e-dep-${uniqueId}` },
        data: { amount: 100, method: 'test' }
    });

    // 2. Login UI
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/$/, { timeout: 10000 });

    // 3. Play Game
    await page.click('.group');
    await expect(page).toHaveURL(/\/game\//);
    
    // 4. Spin (Trigger Signed Callback)
    await expect(page.locator('text=BAL: $100.00')).toBeVisible();
    await page.click('button:has-text("SPIN")');
    
    // 5. Verify Balance Change
    await expect.poll(async () => {
        const text = await page.locator('div.font-mono:has-text("BAL:")').first().innerText();
        return text;
    }, { timeout: 15000 }).not.toBe('BAL: $100.00');
    
    console.log('Secure Game Loop PASS');
  });
});
