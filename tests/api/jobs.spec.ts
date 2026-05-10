import { test, expect } from '@playwright/test';

test.describe('Jobs API endpoints', () => {
  const endpoint = '/jobs';
  const validToken = 'Bearer test-token';
  const validPayload = { type: 'backtest', params: { strategy: 'momentum' } };
  
  test('POST /jobs with valid payload and auth', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: validPayload,
      headers: { 'Authorization': validToken }
    });
    expect(response.ok()).toBeTruthy();
  });

  test('POST /jobs with invalid payload', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: { invalid: 'data' },
      headers: { 'Authorization': validToken }
    });
    expect(response.status()).toBe(422);
  });

  test('POST /jobs with missing auth', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: validPayload
    });
    expect(response.status()).toBe(401);
  });

  test('POST /jobs with invalid IP', async ({ request }) => {
    const response = await request.post(endpoint, {
      data: validPayload,
      headers: {
        'Authorization': validToken,
        'X-Forwarded-For': '192.168.1.100'
      }
    });
    expect(response.status()).toBe(403);
  });
});
