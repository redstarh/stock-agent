export interface DailyPredictionResult {
  stock_code: string;
  stock_name: string | null;
  predicted_direction: 'up' | 'down' | 'neutral';
  predicted_score: number;
  confidence: number;
  actual_direction: 'up' | 'down' | 'neutral' | null;
  actual_change_pct: number | null;
  is_correct: boolean | null;
  news_count: number;
  error_message: string | null;
}

export interface DailyVerificationResponse {
  date: string;
  market: string;
  total: number;
  correct: number;
  accuracy: number;
  results: DailyPredictionResult[];
}

export interface DirectionStats {
  total: number;
  correct: number;
  accuracy: number;
}

export interface DailyTrend {
  date: string;
  accuracy: number;
  total: number;
}

export interface AccuracyResponse {
  period_days: number;
  market: string;
  overall_accuracy: number | null;
  total_predictions: number;
  correct_predictions: number;
  by_direction: {
    up: DirectionStats;
    down: DirectionStats;
    neutral: DirectionStats;
  };
  daily_trend: DailyTrend[];
}

export interface ThemeAccuracy {
  theme: string;
  market: string;
  total_stocks: number;
  correct_count: number;
  accuracy_rate: number;
  avg_predicted_score: number;
  avg_actual_change_pct: number | null;
  rise_index: number | null;
}

export interface ThemeAccuracyResponse {
  date: string;
  themes: ThemeAccuracy[];
}

export interface VerificationStatusResponse {
  status: string;
  last_run: {
    KR?: { date: string; status: string; stocks_verified: number };
    US?: { date: string; status: string; stocks_verified: number };
  };
}
