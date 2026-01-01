import { FullConfig, request as pwRequest, chromium } from '@playwright/test';

const OWNER_EMAIL = process.env.E2E_OWNER_EMAIL || process.env.OWNER_EMAIL || 'admin@casino.com';
const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || process.env.OWNER_PASSWORD || 'Admin123!';
const API_BASE = process.env.E2E_API_BASE || process.env.BACKEND_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.E2E_BASE_URL || process.env.FRONTEND_URL || 'http://localhost:3000';

async function loginWithRetry(apiBaseUrl: string, email: string, password: string): Promise<string> {
  const ctx = await pwRequest.newContext({ baseURL: apiBaseUrl });

  let attempt = 0;
  const maxAttempts = 5;

  while (attempt < maxAttempts) {
    attempt += 1;
    const res = await ctx.post('/api/v1/auth/login', {
      data: { email, password },
    });

    if (res.status() === 429) {
      // Rate limited: respect Retry-After header or exponential backoff
      const retryAfterHeader = res.headers()['retry-after'];
      let delayMs = 0;
      if (retryAfterHeader) {
        const sec = Number(retryAfterHeader);
        if (!Number.isNaN(sec)) delayMs = sec * 1000;
      }
      if (!delayMs) {
        delayMs = Math.min(30000, 1000 * Math.pow(2, attempt - 1));
      }
      console.warn(`[global-setup] 429 from /auth/login, backing off for ${delayMs}ms (attempt ${attempt})`);
      await new Promise((r) => setTimeout(r, delayMs));
      continue;
    }

    const text = await res.text();
    let json: any = null;
    try {
      json = JSON.parse(text);
    } catch {}

    if (!res.ok()) {
      throw new Error(`[global-setup] admin login failed ${res.status()} body=${text}`);
    }

    const token =
      json?.access_token || json?.token || json?.data?.access_token || json?.data?.token;
    if (!token) {
      throw new Error(`[global-setup] admin login response missing token: ${JSON.stringify(json)}`);
    }

    return token as string;
  }

  throw new Error('[global-setup] admin login failed after max retries due to rate limiting');
}

export default async function globalSetup(config: FullConfig) {
  const fs = await import('fs');
  const path = await import('path');

  // Always start fresh: remove any cached tokens/storageState that may be expired.
  const authDir = path.resolve(__dirname, '.auth');
  try {
    if (fs.existsSync(authDir)) {
      for (const fn of fs.readdirSync(authDir)) {
        if (
          fn === 'admin-token.json' ||
          fn === 'admin.json' ||
          fn.startsWith('storageState') ||
          fn.endsWith('.json')
        ) {
          try {
            fs.unlinkSync(path.join(authDir, fn));
          } catch {}
        }
      }
    }
  } catch {}

  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const adminToken = await loginWithRetry(API_BASE, OWNER_EMAIL, OWNER_PASSWORD);

  // Persist token for API-based tests
  fs.writeFileSync(path.join(authDir, 'admin-token.json'), JSON.stringify({ token: adminToken }), 'utf-8');
  if (!fs.existsSync(path.join(authDir, 'admin-token.json'))) {
    throw new Error('[global-setup] admin-token.json was not created');
  }

  // Create storageState by performing a real UI login so that
  // localStorage + any auth-related state is consistent with production flows.
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Go directly to login page
  await page.goto(`${FRONTEND_URL}/login`, { waitUntil: 'networkidle' });

  // Fill login form and submit
  await page.fill('#email', OWNER_EMAIL);
  await page.fill('#password', OWNER_PASSWORD);
  
  // Wait for any potential rate limiting to clear
  await page.waitForTimeout(2000);
  
  await page.click('button:has-text("Sign In")');

  // Wait a bit for the login to process and any redirects
  await page.waitForTimeout(8000);

  // Wait until we are no longer on /login and token is present in localStorage
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 45000 });
  await page.waitForFunction(() => !!localStorage.getItem('admin_token'), { timeout: 20000 });

  // Persist storageState for all tests
  await context.storageState({ path: path.join(authDir, 'admin.json') });
  await browser.close();

  if (!fs.existsSync(path.join(authDir, 'admin.json'))) {
    throw new Error('[global-setup] admin.json storageState was not created');
  }
}
