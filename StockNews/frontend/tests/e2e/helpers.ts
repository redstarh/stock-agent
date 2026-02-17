import type { Page } from '@playwright/test';

// Mock data
export const mockTopNews = [
  { stock_code: '005930', stock_name: '삼성전자', news_score: 82.5, sentiment: 'positive', news_count: 15, market: 'KR' },
  { stock_code: '000660', stock_name: 'SK하이닉스', news_score: 71.3, sentiment: 'neutral', news_count: 8, market: 'KR' },
  { stock_code: '035420', stock_name: 'NAVER', news_score: 65.0, sentiment: 'negative', news_count: 5, market: 'KR' },
];

export const mockLatestNews = {
  items: [
    { id: 1, title: '삼성전자 반도체 실적 호조', stock_code: '005930', stock_name: '삼성전자', sentiment: 'positive', news_score: 85.0, source: 'Naver', source_url: null, market: 'KR', theme: '반도체', published_at: '2026-02-18T10:00:00' },
    { id: 2, title: 'SK하이닉스 HBM 수주', stock_code: '000660', stock_name: 'SK하이닉스', sentiment: 'positive', news_score: 78.0, source: 'DART', source_url: null, market: 'KR', theme: '반도체', published_at: '2026-02-18T09:30:00' },
  ],
  total: 2,
  offset: 0,
  limit: 10,
};

export const mockThemes = [
  { theme: '반도체', strength_score: 88.5, news_count: 23, sentiment_avg: 0.45, date: '2026-02-18', market: 'KR' },
  { theme: '2차전지', strength_score: 72.1, news_count: 15, sentiment_avg: -0.1, date: '2026-02-18', market: 'KR' },
  { theme: 'AI/로봇', strength_score: 65.3, news_count: 10, sentiment_avg: 0.6, date: '2026-02-18', market: 'KR' },
];

export const mockNewsScore = {
  stock_code: '005930',
  stock_name: '삼성전자',
  news_score: 82.5,
  recency: 0.9,
  frequency: 0.75,
  sentiment_score: 0.6,
  disclosure: 0.3,
  news_count: 15,
};

export const mockTimeline = [
  { date: '2026-02-12', score: 70.0 },
  { date: '2026-02-13', score: 72.5 },
  { date: '2026-02-14', score: 75.0 },
  { date: '2026-02-15', score: 78.0 },
  { date: '2026-02-16', score: 80.0 },
  { date: '2026-02-17', score: 81.0 },
  { date: '2026-02-18', score: 82.5 },
];

/** Set up API route mocks for all endpoints */
export async function setupApiMocks(page: Page) {
  await page.route('**/api/v1/news/top*', async (route) => {
    await route.fulfill({ json: mockTopNews });
  });

  await page.route('**/api/v1/news/latest*', async (route) => {
    await route.fulfill({ json: mockLatestNews });
  });

  await page.route('**/api/v1/theme/strength*', async (route) => {
    await route.fulfill({ json: mockThemes });
  });

  await page.route('**/api/v1/news/score*', async (route) => {
    await route.fulfill({ json: mockNewsScore });
  });

  await page.route('**/api/v1/stocks/*/timeline*', async (route) => {
    await route.fulfill({ json: mockTimeline });
  });
}
