/** 감성 분석 결과 */
export type Sentiment = 'positive' | 'neutral' | 'negative';

/** 뉴스 개별 항목 */
export interface NewsItem {
  id: number;
  title: string;
  stock_code: string;
  stock_name: string | null;
  sentiment: Sentiment;
  sentiment_score?: number;
  news_score: number;
  source: string;
  source_url: string | null;
  market: string;
  theme: string | null;
  summary?: string | null;
  published_at: string | null;
}

/** 종목별 뉴스 스코어 */
export interface NewsScore {
  stock_code: string;
  stock_name: string | null;
  news_score: number;
  recency: number;
  frequency: number;
  sentiment_score: number;
  disclosure: number;
  news_count: number;
  top_themes?: string[];
  updated_at?: string | null;
}

/** Top 종목 뉴스 요약 */
export interface NewsTopItem {
  stock_code: string;
  stock_name: string | null;
  news_score: number;
  sentiment: Sentiment;
  news_count: number;
  market: string;
}

/** 스코어 타임라인 포인트 */
export interface TimelinePoint {
  date: string;
  score: number;
}

/** 예측 데이터 */
export interface PredictionData {
  stock_code: string;
  prediction_score: number | null;
  direction: 'up' | 'down' | 'neutral' | null;
  confidence: number | null;
  based_on_days: number;
}
