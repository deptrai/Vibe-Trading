import { test, expect } from '@playwright/test';
import { apiRequest } from '../utils/api';

test.describe('Health & Metadata APIs', () => {
  test('GET /health returns healthy status', async () => {
    const response = await apiRequest.get('/health');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('GET /api returns metadata', async () => {
    const response = await apiRequest.get('/api');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.service).toBe('Vibe-Trading API');
  });

  test('GET /skills returns registered skills', async () => {
    const response = await apiRequest.get('/skills');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });
});