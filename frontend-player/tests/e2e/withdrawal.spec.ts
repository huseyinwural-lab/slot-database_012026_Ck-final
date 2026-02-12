import { test, expect } from '@playwright/test';

test.describe('P0 Withdrawal Flow', () => {
  let playerContext;
  let playerPage;
  let adminContext;
  let adminPage;
  
  const timestamp = Date.now();
  const playerEmail = `withdraw_${timestamp}@test.com`;
  const adminEmail = "admin@casino.com";
  const adminPass = "Admin123!";

  test.beforeAll(async ({ browser, request }) => {
    // 1. Setup Backend: Ensure Healthy
    const health = await request.get('/api/health');
    expect(health.ok()).toBeTruthy();
    
    // 2. Register Player via API (Shortcut)
    await request.post('/api/v1/auth/player/register', {
        data: {
            email: playerEmail,
            password: "Password123!",
            username: `user_${timestamp}`,
            phone: "+15550009999",
            dob: "1990-01-01"
        }
    });
    
    // 3. Login & Get Token to Verify & Deposit
    const loginRes = await request.post('/api/v1/auth/player/login', {
        data: { email: playerEmail, password: "Password123!" }
    });
    const loginData = await loginRes.json();
    const token = loginData.access_token;
    
    // 4. Verify Mock
    await request.post('/api/v1/verify/email/send', { data: { email: playerEmail }, headers: { Authorization: `Bearer ${token}` } });
    await request.post('/api/v1/verify/email/confirm', { data: { email: playerEmail, code: "123456" }, headers: { Authorization: `Bearer ${token}` } });
    await request.post('/api/v1/verify/sms/send', { data: { phone: "+15550009999" }, headers: { Authorization: `Bearer ${token}` } });
    await request.post('/api/v1/verify/sms/confirm', { data: { phone: "+15550009999", code: "123456" }, headers: { Authorization: `Bearer ${token}` } });

    // 5. Deposit 500
    await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": `dep_${timestamp}` }
    });
  });

  test('Player Request -> Admin Approve', async ({ browser }) => {
    // --- Player Context ---
    playerContext = await browser.newContext();
    playerPage = await playerContext.newPage();
    
    // Login
    await playerPage.goto('/login');
    await playerPage.locator('input[type="email"]').fill(playerEmail);
    await playerPage.locator('input[type="password"]').fill("Password123!");
    await playerPage.getByRole('button', { name: /Login|Giriş/i }).click();
    await expect(playerPage).toHaveURL(/\/lobby/);
    
    // Go to Wallet
    await playerPage.goto('/wallet');
    // Check balance 500
    await expect(playerPage.getByText('500')).toBeVisible(); 
    
    // Request Withdrawal (Assume UI updated)
    // If UI not ready, this will fail - expecting Dev to implement UI in this task.
    // Assuming "Withdraw" tab or button.
    // For now, let's verify API level via curl/request if UI is missing, OR implementing UI is part of task.
    // Task said: "Player Withdrawal UI (Faz 2.1)". So I must assume I built it.
    
    // Click "Withdraw" tab/button
    // (I need to implement this in WalletPage.jsx first)
  });
});
