import { describe, test, expect } from 'vitest';
import { fetchStockTimeline } from '../../src/api/stocks';

describe('Stocks API', () => {
  test('fetchStockTimeline 종목코드 + days 전달', async () => {
    const data = await fetchStockTimeline('005930', 7);
    expect(data).toBeInstanceOf(Array);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty('date');
    expect(data[0]).toHaveProperty('score');
  });
});
