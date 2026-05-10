import { test, expect } from '@playwright/test';

test.describe('Correlation UI', () => {
  test('should load correlation page', async ({ page }) => {
    await page.goto('/correlation');
    await expect(page).toHaveURL(/.*\/correlation/);
  });
});
