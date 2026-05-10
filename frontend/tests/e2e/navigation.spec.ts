import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to all main routes', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*\//);
    await page.goto('/agent');
    await expect(page).toHaveURL(/.*\/agent/);
    await page.goto('/settings');
    await expect(page).toHaveURL(/.*\/settings/);
    await page.goto('/compare');
    await expect(page).toHaveURL(/.*\/compare/);
    await page.goto('/correlation');
    await expect(page).toHaveURL(/.*\/correlation/);
  });
});
