import { describe, test, expect } from 'vitest';
import { API_BASE_URL, DEFAULT_TIMEOUT, ApiError } from '../../src/api/client';

describe('API Client', () => {
  test('base URL이 /api/v1로 설정됨', () => {
    expect(API_BASE_URL).toBe('/api/v1');
  });

  test('타임아웃 설정 확인', () => {
    expect(DEFAULT_TIMEOUT).toBe(10_000);
  });

  test('ApiError에 status 포함', () => {
    const err = new ApiError(404, 'Not Found');
    expect(err.status).toBe(404);
    expect(err.message).toBe('Not Found');
    expect(err.name).toBe('ApiError');
  });
});
