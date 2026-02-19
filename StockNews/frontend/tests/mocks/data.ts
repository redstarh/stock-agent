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

export const mockStockTimeline = (_code: string) => [
  { date: '2024-01-09', score: 60.2 },
  { date: '2024-01-10', score: 65.1 },
  { date: '2024-01-11', score: 70.3 },
  { date: '2024-01-12', score: 68.5 },
  { date: '2024-01-13', score: 75.2 },
  { date: '2024-01-14', score: 80.1 },
  { date: '2024-01-15', score: 85.5 },
];

export const mockThemeStrength = () => [
  { theme: 'AI', strength_score: 92.5, news_count: 45, sentiment_avg: 0.7, date: '2024-01-15', market: 'KR' },
  { theme: '반도체', strength_score: 88.3, news_count: 38, sentiment_avg: 0.6, date: '2024-01-15', market: 'KR' },
  { theme: '2차전지', strength_score: 65.1, news_count: 22, sentiment_avg: -0.2, date: '2024-01-15', market: 'KR' },
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
