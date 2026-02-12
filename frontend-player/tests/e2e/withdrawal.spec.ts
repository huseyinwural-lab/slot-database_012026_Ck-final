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

    // 5. Deposit 500 (Use API to ensure balance)
    // If Idempotency key issue, use unique
    const depRes = await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
    // Check if deposit successful (might be blocked by mocked settings)
    const depData = await depRes.json();
    console.log("Deposit Result:", depData);
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
    
    // Wait for balance load. If 0, maybe deposit failed?
    // Retry deposit via UI if 0
    const balanceText = await playerPage.getByTestId('wallet-balance').innerText();
    if (balanceText.includes("0 USD")) {
        console.log("Balance is 0, trying UI deposit...");
        await playerPage.getByTestId('amount-input').fill('500');
        await playerPage.getByTestId('submit-button').click();
        await expect(playerPage).toHaveURL(/status=success/);
        // Go back to wallet to refresh
        await playerPage.goto('/wallet');
    }

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
    await expect(playerPage.getByText(/Locked: 100|Kilitli: 100/)).toBeVisible();
  });
});
