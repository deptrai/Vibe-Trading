import { test, expect } from '@playwright/test';

test.describe('Compare UI', () => {
  test('should load compare page', async ({ page }) => {
    await page.goto('/compare');
    await expect(page).toHaveURL(/.*\/compare/);
  });
});
