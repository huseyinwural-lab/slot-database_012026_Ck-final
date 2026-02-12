import { test, expect } from '@playwright/test';

test.describe('P0 Withdrawal Flow', () => {
  let playerContext;
  let playerPage;
  
  const timestamp = Date.now();
  const playerEmail = `withdraw_${timestamp}@test.com`;
  const playerPhone = `+1555${timestamp.toString().slice(-7)}`;

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
            phone: playerPhone,
            dob: "1990-01-01"
        }
    });
    
    // 3. Login
    const loginRes = await request.post('/api/v1/auth/player/login', {
        data: { email: playerEmail, password: "Password123!" }
    });
    const loginData = await loginRes.json();
    const token = loginData.access_token;
    
    const headers = { Authorization: `Bearer ${token}` };
    
    // 4. Verify Email/SMS
    await request.post('/api/v1/verify/email/send', { data: { email: playerEmail }, headers });
    await request.post('/api/v1/verify/email/confirm', { data: { email: playerEmail, code: "123456" }, headers });
    await request.post('/api/v1/verify/sms/send', { data: { phone: playerPhone }, headers });
    await request.post('/api/v1/verify/sms/confirm', { data: { phone: playerPhone, code: "123456" }, headers });

    // 5. Force KYC Verified (Test Backdoor)
    await request.post('/api/v1/test/set-kyc', { data: { email: playerEmail, status: "verified" } });

    // 6. Deposit 500
    const depRes = await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
    
    expect(depRes.ok()).toBeTruthy();
  });

  test('Player Request -> Admin Approve', async ({ browser }) => {
    playerContext = await browser.newContext();
    playerPage = await playerContext.newPage();
    
    await playerPage.goto('/login');
    await playerPage.getByTestId('login-email-input').fill(playerEmail);
    await playerPage.getByTestId('login-password-input').fill("Password123!");
    await playerPage.getByTestId('login-submit-button').click();
    await expect(playerPage).toHaveURL(/\/lobby/);
    
    await playerPage.goto('/wallet');
    
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('500');
    
    await playerPage.getByTestId('tab-withdraw').click();
    await playerPage.getByTestId('amount-input').fill('100');
    await playerPage.getByTestId('address-input').fill('TR123456');
    await playerPage.getByTestId('submit-button').click();
    
    // Wait for update
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('400');
    await expect(playerPage.getByText(/Locked: 100|Kilitli: 100/i)).toBeVisible();
  });
});
