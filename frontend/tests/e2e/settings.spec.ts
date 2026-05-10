import { test, expect } from '@playwright/test';

test.describe('Settings UI', () => {
  test('should load settings and show providers', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.getByText('LLM Connection')).toBeVisible();
    const providerSelect = page.locator('select').first();
    await expect(providerSelect).toBeVisible();
  });
});
