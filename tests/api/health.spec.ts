import { test, expect } from '@playwright/test';

test.describe('Health API endpoints', () => {
  test('GET /health returns 200 OK', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.ok()).toBeTruthy();
  });
});
