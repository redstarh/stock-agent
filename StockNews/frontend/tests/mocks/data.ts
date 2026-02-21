/**
 * Mock 데이터 — 전체 API 응답에 사용
 */

export const mockNewsTop = (market: string = 'KR') => [
  {
    stock_code: market === 'KR' ? '005930' : 'AAPL',
    stock_name: market === 'KR' ? '삼성전자' : 'Apple',
    news_score: 85.5,
    sentiment: 'positive',
    news_count: 12,
    market,
    prediction_score: 75.2,
    direction: 'up' as const,
  },
  {
    stock_code: market === 'KR' ? '000660' : 'MSFT',
    stock_name: market === 'KR' ? 'SK하이닉스' : 'Microsoft',
    news_score: 72.3,
    sentiment: 'neutral',
    news_count: 8,
    market,
    prediction_score: 55.8,
    direction: 'neutral' as const,
  },
];

export const mockNewsLatest = () => ({
  items: [
    {
      id: 1,
      title: '삼성전자 실적 발표',
      stock_code: '005930',
      stock_name: '삼성전자',
      sentiment: 'positive',
      news_score: 85.5,
      source: 'naver',
      source_url: 'https://news.naver.com/1',
      market: 'KR',
      published_at: '2024-01-15T09:00:00+09:00',
    },
    {
      id: 2,
      title: 'SK하이닉스 HBM 수주',
      stock_code: '000660',
      stock_name: 'SK하이닉스',
      sentiment: 'positive',
      news_score: 72.3,
      source: 'naver',
      source_url: 'https://news.naver.com/2',
      market: 'KR',
      published_at: '2024-01-15T08:30:00+09:00',
    },
  ],
  total: 2,
  offset: 0,
  limit: 20,
});

export const mockNewsScore = () => ({
  stock_code: '005930',
  stock_name: '삼성전자',
  news_score: 85.5,
  recency: 90,
  frequency: 80,
  sentiment_score: 85,
  disclosure: 100,
  news_count: 12,
});

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const mockStockTimeline = (_code?: string) => [
  { date: '2024-01-09', score: 60.2 },
  { date: '2024-01-10', score: 65.1 },
  { date: '2024-01-11', score: 70.3 },
  { date: '2024-01-12', score: 68.5 },
  { date: '2024-01-13', score: 75.2 },
  { date: '2024-01-14', score: 80.1 },
  { date: '2024-01-15', score: 85.5 },
];

export const mockThemeStrength = () => [
  { theme: 'AI', strength_score: 92.5, news_count: 45, sentiment_avg: 0.7, rise_index: 75.0, date: '2024-01-15', market: 'KR' },
  { theme: '반도체', strength_score: 88.3, news_count: 38, sentiment_avg: 0.6, rise_index: 68.0, date: '2024-01-15', market: 'KR' },
  { theme: '2차전지', strength_score: 65.1, news_count: 22, sentiment_avg: -0.2, rise_index: 42.0, date: '2024-01-15', market: 'KR' },
];

export const mockPrediction = (code: string) => {
  if (code === 'INVALID') {
    return null; // Will trigger error in handler
  }
  return {
    stock_code: code,
    prediction_score: 72.5,
    direction: 'up' as const,
    confidence: 0.85,
    based_on_days: 7,
  };
};

export const mockAccuracy = () => ({
  period_days: 30,
  market: 'KR',
  overall_accuracy: 75.5,
  total_predictions: 100,
  correct_predictions: 75,
  by_direction: {
    up: { total: 40, correct: 32, accuracy: 80.0 },
    down: { total: 35, correct: 28, accuracy: 80.0 },
    neutral: { total: 25, correct: 15, accuracy: 60.0 },
  },
  daily_trend: [
    { date: '2024-01-10', accuracy: 70.0, total: 10 },
    { date: '2024-01-11', accuracy: 75.0, total: 12 },
    { date: '2024-01-12', accuracy: 80.0, total: 15 },
  ],
});

export const mockDailyResults = () => ({
  date: '2024-01-15',
  market: 'KR',
  total: 3,
  correct: 2,
  accuracy: 66.7,
  results: [
    {
      stock_code: '005930',
      stock_name: '삼성전자',
      predicted_direction: 'up' as const,
      predicted_score: 85.5,
      confidence: 0.85,
      actual_direction: 'up' as const,
      actual_change_pct: 2.5,
      is_correct: true,
      news_count: 12,
      error_message: null,
    },
    {
      stock_code: '000660',
      stock_name: 'SK하이닉스',
      predicted_direction: 'down' as const,
      predicted_score: 72.3,
      confidence: 0.75,
      actual_direction: 'up' as const,
      actual_change_pct: 1.2,
      is_correct: false,
      news_count: 8,
      error_message: null,
    },
    {
      stock_code: '035720',
      stock_name: '카카오',
      predicted_direction: 'neutral' as const,
      predicted_score: 55.0,
      confidence: 0.60,
      actual_direction: 'neutral' as const,
      actual_change_pct: 0.1,
      is_correct: true,
      news_count: 5,
      error_message: null,
    },
  ],
});

export const mockThemeAccuracy = () => ({
  date: '2024-01-15',
  themes: [
    {
      theme: 'AI',
      market: 'KR',
      total_stocks: 15,
      correct_count: 12,
      accuracy_rate: 80.0,
      avg_predicted_score: 75.5,
      avg_actual_change_pct: 2.5,
      rise_index: 70.0,
    },
    {
      theme: '반도체',
      market: 'KR',
      total_stocks: 20,
      correct_count: 14,
      accuracy_rate: 70.0,
      avg_predicted_score: 72.3,
      avg_actual_change_pct: 1.8,
      rise_index: 65.0,
    },
    {
      theme: '2차전지',
      market: 'KR',
      total_stocks: 12,
      correct_count: 5,
      accuracy_rate: 41.7,
      avg_predicted_score: 60.0,
      avg_actual_change_pct: -0.5,
      rise_index: 45.0,
    },
  ],
});
