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
  { theme: '반도체', strength_score: 88.5, news_count: 23, sentiment_avg: 0.45, rise_index: 72.0, date: '2026-02-18', market: 'KR' },
  { theme: '2차전지', strength_score: 72.1, news_count: 15, sentiment_avg: -0.1, rise_index: 48.0, date: '2026-02-18', market: 'KR' },
  { theme: 'AI/로봇', strength_score: 65.3, news_count: 10, sentiment_avg: 0.6, rise_index: 65.0, date: '2026-02-18', market: 'KR' },
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

export const mockPrediction = {
  stock_code: '005930',
  prediction_score: 72.5,
  direction: 'up' as const,
  confidence: 0.85,
  based_on_days: 7,
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

export const mockAccuracyData = {
  period_days: 30,
  market: 'KR',
  overall_accuracy: 72.5,
  total_predictions: 120,
  correct_predictions: 87,
  by_direction: {
    up: { total: 50, correct: 38, accuracy: 76.0 },
    down: { total: 45, correct: 32, accuracy: 71.1 },
    neutral: { total: 25, correct: 17, accuracy: 68.0 },
  },
  daily_trend: [
    { date: '2026-02-12', accuracy: 70.0, total: 15 },
    { date: '2026-02-13', accuracy: 68.5, total: 18 },
    { date: '2026-02-14', accuracy: 72.0, total: 20 },
    { date: '2026-02-15', accuracy: 75.5, total: 17 },
    { date: '2026-02-16', accuracy: 71.0, total: 22 },
    { date: '2026-02-17', accuracy: 73.5, total: 16 },
    { date: '2026-02-18', accuracy: 74.0, total: 12 },
  ],
};

export const mockDailyResults = {
  date: '2026-02-18',
  market: 'KR',
  total: 5,
  correct: 4,
  accuracy: 80.0,
  results: [
    {
      stock_code: '005930',
      stock_name: '삼성전자',
      predicted_direction: 'up' as const,
      predicted_score: 85.5,
      confidence: 0.82,
      actual_direction: 'up' as const,
      actual_change_pct: 2.3,
      is_correct: true,
      news_count: 15,
      error_message: null,
    },
    {
      stock_code: '000660',
      stock_name: 'SK하이닉스',
      predicted_direction: 'up' as const,
      predicted_score: 78.0,
      confidence: 0.75,
      actual_direction: 'down' as const,
      actual_change_pct: -1.2,
      is_correct: false,
      news_count: 8,
      error_message: null,
    },
    {
      stock_code: '035420',
      stock_name: 'NAVER',
      predicted_direction: 'down' as const,
      predicted_score: 45.0,
      confidence: 0.68,
      actual_direction: 'down' as const,
      actual_change_pct: -0.8,
      is_correct: true,
      news_count: 5,
      error_message: null,
    },
    {
      stock_code: '051910',
      stock_name: 'LG화학',
      predicted_direction: 'neutral' as const,
      predicted_score: 55.0,
      confidence: 0.60,
      actual_direction: 'neutral' as const,
      actual_change_pct: 0.1,
      is_correct: true,
      news_count: 3,
      error_message: null,
    },
    {
      stock_code: '005380',
      stock_name: '현대차',
      predicted_direction: 'up' as const,
      predicted_score: 72.0,
      confidence: 0.71,
      actual_direction: 'up' as const,
      actual_change_pct: 1.5,
      is_correct: true,
      news_count: 6,
      error_message: null,
    },
  ],
};

export const mockThemeAccuracy = {
  date: '2026-02-18',
  themes: [
    {
      theme: '반도체',
      market: 'KR',
      total_stocks: 12,
      correct_count: 9,
      accuracy_rate: 75.0,
      avg_predicted_score: 78.5,
      avg_actual_change_pct: 1.8,
      rise_index: 72.0,
    },
    {
      theme: '2차전지',
      market: 'KR',
      total_stocks: 8,
      correct_count: 5,
      accuracy_rate: 62.5,
      avg_predicted_score: 65.0,
      avg_actual_change_pct: -0.5,
      rise_index: 48.0,
    },
    {
      theme: 'AI/로봇',
      market: 'KR',
      total_stocks: 6,
      correct_count: 5,
      accuracy_rate: 83.3,
      avg_predicted_score: 82.0,
      avg_actual_change_pct: 2.1,
      rise_index: 65.0,
    },
    {
      theme: '자동차',
      market: 'KR',
      total_stocks: 10,
      correct_count: 7,
      accuracy_rate: 70.0,
      avg_predicted_score: 68.5,
      avg_actual_change_pct: 0.8,
      rise_index: 55.0,
    },
  ],
};

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

  await page.route('**/api/v1/stocks/*/prediction*', async (route) => {
    await route.fulfill({ json: mockPrediction });
  });

  await page.route('**/api/v1/verification/accuracy*', async (route) => {
    await route.fulfill({ json: mockAccuracyData });
  });

  await page.route('**/api/v1/verification/daily*', async (route) => {
    await route.fulfill({ json: mockDailyResults });
  });

  await page.route('**/api/v1/verification/themes*', async (route) => {
    await route.fulfill({ json: mockThemeAccuracy });
  });
}
