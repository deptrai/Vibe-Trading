import { test, expect } from '@playwright/test';

test.describe('Agent UI', () => {
  test('should show agent input and allow typing', async ({ page }) => {
    await page.goto('/agent');
    const input = page.locator('textarea');
    await expect(input).toBeVisible();
    await input.fill('Hello Agent');
    await expect(input).toHaveValue('Hello Agent');
  });
});
