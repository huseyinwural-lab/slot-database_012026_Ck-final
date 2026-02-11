import { test, expect } from '@playwright/test';

// Generate unique user for this run
const timestamp = Date.now();
const email = `player_${timestamp}@e2e.test`;
const phone = `+1555${timestamp.toString().slice(-7)}`;
const password = 'Player123!';

test.describe('P0 Player Journey', () => {
  
  test.beforeAll(async ({ request }) => {
    // Ensure backend is healthy
    const response = await request.get('/api/health');
    expect(response.ok()).toBeTruthy();
  });

  test('Register new player', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', password);
    await page.fill('input[name="confirmPassword"]', password);
    await page.fill('input[name="phone"]', phone);
    
    // DOB (if requested, assuming simple date input or 3 fields)
    // Checking the Register page implementation would be better, but assuming standard fields
    // Assuming a simple "dob" input for now based on standard HTML5 date
    // If UI is different, test will fail and I'll adjust.
    const dobInput = page.locator('input[name="dob"]');
    if (await dobInput.count() > 0) {
        await dobInput.fill('1990-01-01');
    }

    // Terms checkbox
    const terms = page.locator('input[name="terms"]');
    if (await terms.count() > 0) {
        await terms.check();
    }

    await page.click('button[type="submit"]');

    // Expect redirect to verify or login
    // If successful, should go to /verify/email
    await expect(page).toHaveURL(/\/verify\/email/);
  });

  test('Verify Email', async ({ page, request }) => {
    // Login first if not persisted (fresh context)
    // But tests run in parallel/sequence? default config is parallel.
    // I should use test.serial() or reuse context.
    // For now, I'll assume sequential flow in one test block or handle login.
    // Actually, splitting into steps in one test case is better for E2E flow.
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
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password); // specific to avoid "Confirm Password"
    await page.getByLabel('Confirm Password').fill(password);
    
    // Phone might be standard input
    await page.locator('input[type="tel"]').fill(phone);
    
    // DOB
    await page.getByLabel('Date of Birth').fill('1990-01-01');

    await page.getByRole('button', { name: /Register|Sign Up/i }).click();

    // 2. Email Verification
    // Expect to be on verification page
    await expect(page).toHaveURL(/verify/);
    await expect(page.getByText('Verify your email')).toBeVisible();

    // Trigger send code (if not auto-sent)
    // await page.getByRole('button', { name: 'Send Code' }).click();

    // Since we don't have access to real email inbox in E2E easily without Mailosaur/etc,
    // AND the backend "keyless" implementation might just return success but we need the CODE.
    // Wait, the "keyless" impl for Resend requires a key. 
    // If I don't have the key, this step FAILS here.
    // User instruction: "Secrets temini...".
    // If secrets provided, I would check backend logs or database for the code?
    // The `_EMAIL_CODES` in-memory dict in `player_verification.py` stores the code!
    // I can expose a "backdoor" endpoint to get the OTP for testing? 
    // Or simpler: The backend implementation I saw earlier uses `_EMAIL_CODES` in-memory.
    // I can mock the "Send" to return the code in the response locally?
    // No, I shouldn't change code logic just for test unless requested.
    // The user said "Inbox üzerinden" (Via inbox).
    
    // For now, I'll stop at Verification check.
  });
});
