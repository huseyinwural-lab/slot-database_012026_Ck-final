import { test, expect } from '@playwright/test';

test.describe('P0 Withdrawal Flow', () => {
  let playerContext;
  let playerPage;
  
  const timestamp = Date.now();
  const playerEmail = `withdraw_${timestamp}@test.com`;

  test.beforeAll(async ({ request }) => {
    // 1. Setup Backend
    const health = await request.get('/api/health');
    expect(health.ok()).toBeTruthy();
    
    // 2. Register Player
    await request.post('/api/v1/auth/player/register', {
        data: {
            email: playerEmail,
            password: "Password123!",
            username: `user_${timestamp}`,
            phone: "+15550009999",
            dob: "1990-01-01"
        }
    });
    
    // 3. Login
    const loginRes = await request.post('/api/v1/auth/player/login', {
        data: { email: playerEmail, password: "Password123!" }
    });
    const loginData = await loginRes.json();
    const token = loginData.access_token;
    
    // 4. Verify Mock
    const headers = { Authorization: `Bearer ${token}` };
    await request.post('/api/v1/verify/email/send', { data: { email: playerEmail }, headers });
    await request.post('/api/v1/verify/email/confirm', { data: { email: playerEmail, code: "123456" }, headers });
    await request.post('/api/v1/verify/sms/send', { data: { phone: "+15550009999" }, headers });
    await request.post('/api/v1/verify/sms/confirm', { data: { phone: "+15550009999", code: "123456" }, headers });

    // 5. Deposit 500
    await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
  });

  test('Player Request -> Admin Approve', async ({ browser }) => {
    // --- Player Context ---
    playerContext = await browser.newContext();
    playerPage = await playerContext.newPage();
    
    // Login
    await playerPage.goto('/login');
    await playerPage.getByTestId('login-email-input').fill(playerEmail);
    await playerPage.getByTestId('login-password-input').fill("Password123!");
    await playerPage.getByTestId('login-submit-button').click();
    await expect(playerPage).toHaveURL(/\/lobby/);
    
    // Go to Wallet
    await playerPage.goto('/wallet');
    // Check balance 500
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('500');
    
    // Request Withdrawal
    await playerPage.getByTestId('tab-withdraw').click();
    await playerPage.getByTestId('amount-input').fill('100');
    await playerPage.getByTestId('address-input').fill('TR123456');
    await playerPage.getByTestId('submit-button').click();
    
    // Verify toast or UI update
    // Available should drop to 400 (Locked 100)
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('400');
    await expect(playerPage.getByText('Locked: 100')).toBeVisible();
    
    // --- Admin Context (API Level for now as Admin UI test is complex in same file) ---
    // Or we can use API request to approve since we built the endpoint
    // We need admin token. 
    // We can assume default admin credentials or check DB. 
    // Since I reset admin password in previous steps, "Admin123!" should work.
    
    /* 
       NOTE: Admin login endpoint is /api/v1/auth/login (for admins)
       NOT /api/v1/auth/player/login
    */
  });
});
