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
      
      // Auto-filled email? Or need to type? The component shows an input.
      // Usually registration redirects with state, but if not, we assume we need to fill.
      // The Register page calls `register()` which might update store, but VerifyEmail uses local state?
      // `const [email, setEmail] = useState('');` -> It doesn't seem to pre-fill from store in the component code shown!
      // This is a UX bug/gap in the current implementation, but I must work around it for E2E.
      
      await page.getByTestId('verify-email-input').fill(email);
      await page.getByTestId('verify-email-send').click();
      
      // Wait for toast or log
      // In Mock Mode, backend accepts "123456"
      await page.getByTestId('verify-email-code').fill('123456');
      await page.getByTestId('verify-email-confirm').click();

      // 3. SMS Verification
      console.log('Verifying SMS...');
      await expect(page).toHaveURL(/\/verify\/sms/, { timeout: 10000 });
      
      // Same assumption for SMS page, likely need to fill phone if not persisted.
      // Assuming selectors based on email page pattern
      const phoneInput = page.getByPlaceholder(/Phone|Telefon/i);
      if (await phoneInput.count() > 0) {
         await phoneInput.fill(phone);
      }
      
      const sendBtn = page.getByRole('button', { name: /Send|Gönder/i });
      if (await sendBtn.count() > 0) {
        await sendBtn.click();
      }

      await page.getByPlaceholder(/Code|Kod/i).fill('123456');
      await page.getByRole('button', { name: /Verify|Doğrula/i }).click();

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
