import { test, expect } from '@playwright/test';
import { apiRequest } from '../utils/api';

test.describe('Swarm API', () => {
  test('GET /swarm/presets lists available presets', async () => {
    const response = await apiRequest.get('/swarm/presets');
    expect(response.status()).toBe(200);
  });

  test('GET /swarm/runs lists swarm runs', async () => {
    const response = await apiRequest.get('/swarm/runs');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });
});