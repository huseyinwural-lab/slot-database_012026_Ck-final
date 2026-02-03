import { test, expect } from '@playwright/test';

test.describe('P1-1 Nav Integrity (no dead clicks / no 404)', () => {
  test.setTimeout(60000);

  test('ModuleDisabled returns to / (not /dashboard)', async ({ page }) => {
    await page.goto('/module-disabled', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: /Return to Dashboard/i }).click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('Search input is readOnly and does not open CommandDialog', async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });

    const search = page.getByPlaceholder('Global Search (Press Ctrl+K)');
    await expect(search).toBeVisible();

    // Focus should blur immediately; dialog should not appear.
    await search.click();
    await page.waitForTimeout(300);

    await expect(page.getByText('Type to search players, transactions...')).toHaveCount(0);
  });
});
