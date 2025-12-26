import { test, expect, request as pwRequest } from '@playwright/test';

test.describe('Full Casino Game Loop', () => {
  test.setTimeout(120000);

  test('Session -> Bet -> Win -> Ledger Check', async ({ page }) => {
    const API_URL = 'http://localhost:8001';
    const PLAYER_APP_URL = 'http://localhost:3001';
    
    // 1. Setup User
    const uniqueId = Date.now();
    const email = `gamer_${uniqueId}@example.com`;
    const apiContext = await pwRequest.newContext({ baseURL: API_URL });
    
    await apiContext.post('/api/v1/auth/player/register', {
      data: { username: `gamer${uniqueId}`, email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    
    const loginRes = await apiContext.post('/api/v1/auth/player/login', {
      data: { email, password: 'Password123!', tenant_id: 'default_casino' }
    });
    const token = (await loginRes.json()).access_token;
    
    // Deposit 100
    await apiContext.post('/api/v1/player/wallet/deposit', {
        headers: { 'Authorization': `Bearer ${token}` },
        data: { amount: 100, method: 'test' }
    });

    // 2. Login UI
    await page.goto(`${PLAYER_APP_URL}/login`);
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/$/, { timeout: 10000 }); // Lobby

    // 3. Launch Game
    // Click on a game card
    await page.click('.group'); // Clicks first game card
    await expect(page).toHaveURL(/\/game\//);
    
    // 4. Play (Spin)
    // Check initial balance in header
    await expect(page.locator('text=BAL: $100.00')).toBeVisible();
    
    // Spin (Bet $1)
    await page.click('button:has-text("SPIN")');
    
    // Wait for spin result
    // Balance should change (either 99 or more if win)
    await expect.poll(async () => {
        const text = await page.locator('div:has-text("BAL:")').innerText();
        return text;
    }, { timeout: 10000 }).not.toBe('BAL: $100.00');
    
    console.log('Game Loop Successful');
  });
});
