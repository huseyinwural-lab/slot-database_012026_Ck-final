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
    
    // 4. Verify Mock (Crucial: Must succeed for deposit)
    const headers = { Authorization: `Bearer ${token}` };
    
    // Ensure mock mode is ON in backend or this will fail
    // If backend is not in mock mode, we can't verify easily without real keys.
    // Assuming backend respects MOCK_EXTERNAL_SERVICES=true which we set.
    
    await request.post('/api/v1/verify/email/send', { data: { email: playerEmail }, headers });
    await request.post('/api/v1/verify/email/confirm', { data: { email: playerEmail, code: "123456" }, headers });
    await request.post('/api/v1/verify/sms/send', { data: { phone: "+15550009999" }, headers });
    await request.post('/api/v1/verify/sms/confirm', { data: { phone: "+15550009999", code: "123456" }, headers });

    // 5. Deposit 500 (Use API to ensure balance)
    const depRes = await request.post('/api/v1/player/wallet/deposit', {
        data: { amount: 500, currency: "USD", method: "test" },
        headers: { ...headers, "Idempotency-Key": `dep_${timestamp}` }
    });
    const depData = await depRes.json();
    console.log("Deposit Result:", JSON.stringify(depData));
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
    
    // Check balance 500. 
    // If deposit failed in beforeAll due to verification lag, retry here.
    // The previous run showed "AUTH_UNVERIFIED".
    // This means beforeAll verification calls didn't propagate or mock verification failed.
    
    const balanceText = await playerPage.getByTestId('wallet-balance').innerText();
    if (balanceText.includes("0 USD")) {
        console.log("Balance 0, retrying verification & deposit via UI...");
        
        // Maybe verification failed? Check verify status in UI?
        // Hard to check. Let's assume we need to verify.
        // But login redirect to lobby implies verification pass? No, login allowed but deposit blocked.
        
        // Try deposit again
        await playerPage.getByTestId('amount-input').fill('500');
        await playerPage.getByTestId('submit-button').click();
        
        // If unverified, toast should appear.
        // If verified, redirect.
        try {
            await expect(playerPage).toHaveURL(/status=success/, { timeout: 5000 });
        } catch {
            console.log("UI Deposit failed (likely unverified). Skipping withdraw test.");
            // If we can't deposit, we can't withdraw. Test fails gracefully or we fix verification logic.
            // Force fail to debug
            throw new Error("Could not deposit funds. Verification likely failed.");
        }
        
        await playerPage.goto('/wallet');
    }

    await expect(playerPage.getByTestId('wallet-balance')).toContainText('500');
    
    // Request Withdrawal
    await playerPage.getByTestId('tab-withdraw').click();
    await playerPage.getByTestId('amount-input').fill('100');
    await playerPage.getByTestId('address-input').fill('TR123456');
    await playerPage.getByTestId('submit-button').click();
    
    // Verify toast or UI update
    await expect(playerPage.getByTestId('wallet-balance')).toContainText('400');
    
    // Check locked text (handling case insensitive or slight copy variations)
    // "Locked: 100 USD"
    await expect(playerPage.locator('text=/Locked.*100/i')).toBeVisible();
  });
});
