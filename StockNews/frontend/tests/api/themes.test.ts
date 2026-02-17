import { describe, test, expect } from 'vitest';
import { fetchThemeStrength } from '../../src/api/themes';

describe('Themes API', () => {
  test('fetchThemeStrength 데이터 반환', async () => {
    const data = await fetchThemeStrength('KR');
    expect(data).toBeInstanceOf(Array);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty('theme');
    expect(data[0]).toHaveProperty('strength_score');
  });
});
