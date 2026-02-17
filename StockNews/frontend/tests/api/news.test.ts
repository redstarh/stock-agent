import { describe, test, expect } from 'vitest';
import { fetchTopNews, fetchLatestNews, fetchNewsScore } from '../../src/api/news';

describe('News API', () => {
  test('fetchTopNews가 올바른 데이터 반환', async () => {
    const data = await fetchTopNews('KR');
    expect(data).toBeInstanceOf(Array);
    expect(data.length).toBeGreaterThan(0);
    expect(data[0]).toHaveProperty('stock_code');
    expect(data[0]).toHaveProperty('news_score');
  });

  test('fetchLatestNews 페이지네이션 응답', async () => {
    const data = await fetchLatestNews(0, 20);
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data.items).toBeInstanceOf(Array);
  });

  test('fetchNewsScore 종목코드 전달', async () => {
    const data = await fetchNewsScore('005930');
    expect(data.stock_code).toBe('005930');
    expect(data).toHaveProperty('news_score');
  });
});
