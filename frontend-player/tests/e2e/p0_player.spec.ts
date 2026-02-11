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
      
      await page.getByTestId('verify-email-input').fill(email);
      await page.getByTestId('verify-email-send').click();
      await page.waitForTimeout(1000);
      
      await page.getByTestId('verify-email-code').fill('123456');
      await page.getByTestId('verify-email-confirm').click();
      await page.waitForTimeout(1000);

      // 3. SMS Verification
      console.log('Verifying SMS...');
      await expect(page).toHaveURL(/\/verify\/sms/, { timeout: 10000 });
      
      const phoneInput = page.getByPlaceholder(/Phone|Telefon/i);
      if (await phoneInput.count() > 0) {
         await phoneInput.fill(phone);
      }
      const sendBtn = page.getByRole('button', { name: /Kodu Gönder|Send/i });
      if (await sendBtn.count() > 0) {
        await sendBtn.click();
      }
      await page.waitForTimeout(1000);

      await page.getByPlaceholder(/Code|Doğrulama Kodu/i).fill('123456');
      await page.getByRole('button', { name: /Verify|Doğrula/i }).click();
      await page.waitForTimeout(1000);

      // 4. Login
      console.log('Logging In...');
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
      
      await page.getByTestId('login-email-input').fill(email);
      await page.getByTestId('login-password-input').fill(password);
      await page.getByTestId('login-submit-button').click();

      // 5. Lobby
      console.log('Entering Lobby...');
      await expect(page).toHaveURL(/\/lobby/, { timeout: 10000 });
      // "Featured Games" is the title in H2
      await expect(page.getByTestId('lobby-title')).toHaveText(/Featured Games|Öne Çıkanlar/i);

      // 6. Deposit
      console.log('Testing Deposit...');
      await page.goto('/wallet');
      await expect(page).toHaveURL(/\/wallet/);
      
      const amountInput = page.locator('input[placeholder*="Amount"], input[type="number"]');
      if (await amountInput.count() > 0) {
          await amountInput.fill('100');
          // Assuming there's a deposit button. 
          // If not standard, look for testid if possible or text.
          const btn = page.locator('button').filter({ hasText: /Deposit|Yatır/i });
          if (await btn.count() > 0) {
             await btn.first().click();
          } else {
             // Fallback
             await page.getByRole('button', { name: /Deposit|Yatır/i }).click();
          }
      } else {
          // Maybe a "Deposit" button opens a modal?
          const depositBtn = page.getByRole('button', { name: /Deposit|Para Yatır/i });
          if (await depositBtn.count() > 0) {
              await depositBtn.first().click();
              await page.waitForTimeout(500);
              await page.locator('input[type="number"]').fill('100');
              await page.getByRole('button', { name: /Confirm|Pay|Yatır/i }).click();
          }
      }

      await expect(page).toHaveURL(/status=success/, { timeout: 10000 });
      
      console.log('Deposit Successful (Mock).');
    });
  });
});
