import { test, expect } from '@playwright/test';

test.describe('Vibe-Trading UI E2E', () => {
  test('User enters prompt, clicks Preview, and sees Strategy Preview Card', async ({ page }) => {
    await page.route('**/preview', async route => {
      const json = {
        strategy_name: "Moving Average Crossover",
        parameters: { "fast_period": 10, "slow_period": 50 },
        assets: ["AAPL", "MSFT"]
      };
      await route.fulfill({ json });
    });

    await page.goto('/');

    await page.fill('textarea, input[type="text"]', 'Buy AAPL and MSFT using moving average crossover');
    await page.getByRole('button', { name: /Preview/i }).click();

    await expect(page.getByText('Moving Average Crossover')).toBeVisible();
    await expect(page.getByText('AAPL')).toBeVisible();
  });

  test('User confirms strategy, clicks Run Backtest, and job is submitted', async ({ page }) => {
    await page.route('**/preview', async route => {
      const json = {
        strategy_name: "RSI Strategy",
        parameters: { "rsi_period": 14 },
        assets: ["BTC-USD"]
      };
      await route.fulfill({ json });
    });

    await page.route('**/jobs', async route => {
      const json = {
        job_id: "job-12345",
        status: "pending"
      };
      await route.fulfill({ json });
    });

    await page.route('**/jobs/job-12345', async route => {
      const json = {
        job_id: "job-12345",
        status: "completed",
        result: { "profit": "20%" }
      };
      await route.fulfill({ json });
    });

    await page.goto('/');

    await page.fill('textarea, input[type="text"]', 'Trade BTC-USD using RSI');
    await page.getByRole('button', { name: /Preview/i }).click();

    await page.getByRole('button', { name: /Run Backtest|Confirm/i }).click();

    await expect(page.getByText(/completed/i)).toBeVisible();
  });
});
