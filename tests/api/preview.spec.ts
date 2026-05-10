import { test, expect } from '@playwright/test';

test.describe('Preview API endpoints', () => {
  const endpoint = '/preview';
  const validToken = 'Bearer test-token';
  const validPayload = { strategy: 'mean_reversion' };

  test('POST /preview with valid payload', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: validPayload,
      headers: { 'Authorization': validToken }
    });
    expect(response.ok()).toBeTruthy();
  });

  test('POST /preview with missing auth', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: validPayload
    });
    expect(response.status()).toBe(401);
  });
});
