import { test, expect } from '@playwright/test';
import { apiRequest } from '../utils/api';

test.describe('Sessions API', () => {
  let sessionId = '';

  test('POST /sessions creates a new session', async () => {
    const response = await apiRequest.post('/sessions', { data: { title: 'Test Session' } });
    expect(response.status()).toBe(201);
    const data = await response.json();
    expect(data.title).toBe('Test Session');
    sessionId = data.session_id;
  });

  test('GET /sessions lists sessions', async () => {
    const response = await apiRequest.get('/sessions');
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.some((s: any) => s.session_id === sessionId)).toBe(true);
  });

  test('DELETE /sessions/{session_id} deletes the session', async () => {
    const response = await apiRequest.delete(`/sessions/${sessionId}`);
    expect(response.status()).toBe(200);
  });
});