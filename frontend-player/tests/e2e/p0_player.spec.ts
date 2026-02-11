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

  test('Register new player', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form using data-testid
    await page.getByTestId('register-username-input').fill(username);
    await page.getByTestId('register-email-input').fill(email);
    await page.getByTestId('register-phone-input').fill(phone);
    await page.getByTestId('register-dob-input').fill('1990-01-01');
    await page.getByTestId('register-password-input').fill(password);
    
    // Checkbox
    await page.getByTestId('register-age-checkbox').check();

    // Submit
    await page.getByTestId('register-submit-button').click();

    // Expect redirect to verify/email
    await expect(page).toHaveURL(/\/verify\/email/, { timeout: 10000 });
  });

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
    await page.goto('/register');
    
    await page.getByTestId('register-username-input').fill(`full${timestamp}`);
    await page.getByTestId('register-email-input').fill(`full${email}`);
    await page.getByTestId('register-phone-input').fill(`+15559998888`); // different phone
    await page.getByTestId('register-dob-input').fill('1990-01-01');
    await page.getByTestId('register-password-input').fill(password);
    await page.getByTestId('register-age-checkbox').check();
    
    await page.getByTestId('register-submit-button').click();

    // 2. Email Verification
    await expect(page).toHaveURL(/\/verify\/email/, { timeout: 10000 });
    
    // Stop here as we can't verify easily without secrets/mock
  });
});
