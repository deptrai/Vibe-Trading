import { test, expect } from '@playwright/test';
import { apiRequest } from '../utils/api';

test.describe('Runs API', () => {
  test('GET /runs returns list of runs', async () => {
    const response = await apiRequest.get('/runs?limit=5');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });

  test('GET /runs/{run_id} returns 404 for invalid run', async () => {
    const response = await apiRequest.get('/runs/invalid_run_id');
    expect(response.status()).toBe(404);
  });
});