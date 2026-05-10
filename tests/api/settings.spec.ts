import { test, expect } from '@playwright/test';
import { apiRequest } from '../utils/api';

test.describe('Settings API', () => {
  test('GET /settings/llm returns current LLM settings', async () => {
    const response = await apiRequest.get('/settings/llm');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('provider');
  });

  test('GET /settings/data-sources returns data source settings', async () => {
    const response = await apiRequest.get('/settings/data-sources');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('baostock_supported');
  });
});