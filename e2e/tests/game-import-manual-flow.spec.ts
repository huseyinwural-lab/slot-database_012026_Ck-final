import { test, expect } from '@playwright/test';

test.describe('P0-2 Game Import (manual upload -> preview -> import)', () => {
  test.setTimeout(120000);

  test('JSON upload shows preview and imports into games list', async ({ page }) => {
    // Assumes global-setup created storageState with owner login.
    await page.goto('/games', { waitUntil: 'domcontentloaded' });

    // Navigate to Upload tab
    await page.getByRole('tab', { name: 'Upload' }).click();

    // Select method: Upload HTML5 Game Bundle
    await page.getByText('Method').locator('xpath=following::button[@role="combobox"][1]').click();
    await page.getByRole('option', { name: 'Upload HTML5 Game Bundle' }).click();

    // Choose runtime (HTML5)
    await page.getByRole('button', { name: 'HTML5' }).click();

    // Upload JSON fixture
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles('fixtures/demo_games.json');

    await page.getByRole('button', { name: 'Upload & Analyze' }).click();

    // Preview modal should open
    await expect(page.getByText('Import Preview', { exact: true })).toBeVisible({ timeout: 30000 });

    // Should show at least the 2 demo rows
    await expect(page.getByText('Demo Game 101')).toBeVisible();
    await expect(page.getByText('Demo Game 102')).toBeVisible();

    // Import
    await page.getByRole('button', { name: 'İçe Aktarmayı Başlat' }).click();

    // Switch back to Slots tab and verify games appear.
    await page.getByRole('tab', { name: 'Slots' }).click();

    // Imported games may be categorized; verify by name anywhere on page.
    await expect(page.getByText('Demo Game 101')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Demo Game 102')).toBeVisible({ timeout: 30000 });
  });
});
