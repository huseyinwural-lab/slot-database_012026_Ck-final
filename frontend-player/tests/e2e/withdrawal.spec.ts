import { test, expect } from '@playwright/test';

test.describe('P0 Withdrawal Flow', () => {
  let playerPage;
  
  const timestamp = Date.now();
  const playerEmail = `withdraw_${timestamp}@test.com`;
  const playerPhone = `+1555${timestamp.toString().slice(-7)}`;
  let token;

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
    token = loginData.access_token;
    
    const headers = { Authorization: `Bearer ${token}` };
    
    await request.post('/api/v1/verify/email/send', { data: { email: playerEmail }, headers });
    await request.post('/api/v1/verify/email/confirm', { data: { email: playerEmail, code: "123456" }, headers });
    await request.post('/api/v1/verify/sms/send', { data: { phone: playerPhone }, headers });
    await request.post('/api/v1/verify/sms/confirm', { data: { phone: playerPhone, code: "123456" }, headers });

    // 5. Force KYC Verified
    await request.post('/api/v1/test/set-kyc', { data: { email: playerEmail, status: "verified" } });

    // 6. Deposit 500 (Deterministik)
    await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
  });

  test('Player Request -> API Verify', async ({ browser }) => {
    const context = await browser.newContext();
    playerPage = await context.newPage();
    
    await playerPage.goto('/login');
    await playerPage.getByTestId('login-email-input').fill(playerEmail);
    await playerPage.getByTestId('login-password-input').fill("Password123!");
    await playerPage.getByTestId('login-submit-button').click();
    await expect(playerPage).toHaveURL(/\/lobby/);
    
    await playerPage.goto('/wallet');
    
    // Check initial balance 500
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('500');
    
    await playerPage.getByTestId('tab-withdraw').click();
    await playerPage.getByTestId('amount-input').fill('100');
    await playerPage.getByTestId('address-input').fill('TR123456');
    
    // Step 1: Wait for actual API response
    const withdrawPromise = playerPage.waitForResponse(res =>
      res.url().includes('/api/v1/player/wallet/withdraw') &&
      res.request().method() === 'POST'
    );
    
    await playerPage.getByTestId('submit-button').click();
    
    const withdrawResponse = await withdrawPromise;
    console.log('Withdraw status:', withdrawResponse.status());
    const body = await withdrawResponse.json();
    console.log('Withdraw body:', JSON.stringify(body));

    // Assert 200 OK
    expect(withdrawResponse.status()).toBe(200);
    
    // Assert Body content (Snapshot)
    expect(body.transaction).toBeDefined();
    expect(body.balance).toBeDefined();
    expect(body.balance.available_real).toBe(400); // 500 - 100
    expect(body.balance.held_real).toBe(100);

    // Step 2: Poll API for persistence check (UI independent)
    // We use the test runner's request context, not page request
    const apiContext = await playerPage.context().request;
    
    await expect.poll(async () => {
      const res = await apiContext.get('/api/v1/player/wallet/balance', {
          headers: { Authorization: `Bearer ${token}` }
      });
      const wallet = await res.json();
      return wallet.available_real;
    }, {
      timeout: 5000
    }).toBe(400);

    // Step 3: UI Update Check (Available 400, Locked 100)
    // Now we can trust the backend state is correct, checking if UI reflects it
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('400');
    await expect(playerPage.getByText(/Locked: 100|Kilitli: 100/i)).toBeVisible();
  });
});
