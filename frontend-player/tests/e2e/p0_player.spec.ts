import { test, expect } from '@playwright/test';

// Generate unique user for this run
const timestamp = Date.now();
const email = `player_${timestamp}@e2e.test`;
const phone = `+1555${timestamp.toString().slice(-7)}`;
const password = 'Player123!';
const username = `user${timestamp}`;

test.describe('P0 Player Journey', () => {
  
  test.beforeAll(async ({ request }) => {
    // Ensure backend is healthy
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
  });

  test.describe.serial('Full P0 Funnel', () => {
    let context;
    let page;

    test.beforeAll(async ({ browser }) => {
      context = await browser.newContext();
      page = await context.newPage();
    });

    test.afterAll(async () => {
      await context.close();
    });

    test('Complete Player Journey', async () => {
      // 1. Register
      console.log(`Starting Registration for ${email}`);
      await page.goto('/register');
      
      await page.getByTestId('register-username-input').fill(username);
      await page.getByTestId('register-email-input').fill(email);
      await page.getByTestId('register-phone-input').fill(phone);
      await page.getByTestId('register-dob-input').fill('1990-01-01');
      await page.getByTestId('register-password-input').fill(password);
      await page.getByTestId('register-age-checkbox').check();
      
      await page.getByTestId('register-submit-button').click();

      // 2. Email Verification
      console.log('Verifying Email...');
      await expect(page).toHaveURL(/\/verify\/email/, { timeout: 10000 });
      
      // MUST click Send first to prime the backend mock state
      await page.getByTestId('verify-email-input').fill(email);
      await page.getByTestId('verify-email-send').click();
      
      // Wait a moment for async send
      await page.waitForTimeout(1000);
      
      await page.getByTestId('verify-email-code').fill('123456');
      await page.getByTestId('verify-email-confirm').click();
      
      // Wait for navigation
      await page.waitForTimeout(1000);

      // 3. SMS Verification
      console.log('Verifying SMS...');
      await expect(page).toHaveURL(/\/verify\/sms/, { timeout: 10000 });
      
      // SMS Send
      // Fallback selector strategy for phone input
      const phoneInput = page.getByPlaceholder(/Phone|Telefon/i);
      if (await phoneInput.count() > 0) {
         await phoneInput.fill(phone);
      }
      
      // Send button
      const sendBtn = page.getByRole('button', { name: /Kodu Gönder|Send/i });
      if (await sendBtn.count() > 0) {
        await sendBtn.click();
      }
      
      await page.waitForTimeout(1000);

      await page.getByPlaceholder(/Code|Doğrulama Kodu/i).fill('123456');
      await page.getByRole('button', { name: /Verify|Doğrula/i }).click();
      
      await page.waitForTimeout(1000);

      // 4. Lobby (Game Start Rate KPI)
      console.log('Entering Lobby...');
      await expect(page).toHaveURL(/\/lobby/, { timeout: 10000 });
      await expect(page.getByText(/Lobby|Games/i).first()).toBeVisible();

      // 6. Deposit
      console.log('Testing Deposit...');
      await page.goto('/wallet');
      await expect(page).toHaveURL(/\/wallet/);
      
      // Fill deposit amount
      await page.getByPlaceholder(/Amount/i).fill('100');
      await page.getByRole('button', { name: /Deposit/i }).click();

      // In Mock Mode, backend returns a redirect URL that IS the success URL.
      // So we should be redirected back to wallet with success status.
      await expect(page).toHaveURL(/status=success/);
      
      // Verify balance increased (from 0 to 100)
      await expect(page.getByText('$100')).toBeVisible(); // Approximate check
    });
  });
});
