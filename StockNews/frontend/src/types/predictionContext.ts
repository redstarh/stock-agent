/** 방향별 정확도 */
export interface DirectionAccuracy {
  direction: string;
  total: number;
  correct: number;
  accuracy: number;
  avg_actual_change_pct: number | null;
}

/** 테마별 예측 가능성 */
export interface ThemePredictability {
  theme: string;
  accuracy: number;
  total: number;
  predictability: 'high' | 'medium' | 'low';
}

/** 감성 점수 범위별 분포 */
export interface SentimentRangeBucket {
  range_label: string;
  total: number;
  up_count: number;
  down_count: number;
  neutral_count: number;
  up_ratio: number;
  down_ratio: number;
}

/** 뉴스 건수 효과 */
export interface NewsCountEffect {
  range_label: string;
  total: number;
  accuracy: number;
}

/** Confidence 보정 */
export interface ConfidenceCalibration {
  range_label: string;
  total: number;
  accuracy: number;
}

/** 예측 점수 구간별 분포 */
export interface ScoreRangeBucket {
  range_label: string;
  total: number;
  up_count: number;
  down_count: number;
  neutral_count: number;
}

/** 실패 패턴 */
export interface FailurePattern {
  pattern: string;
  count: number;
  description: string;
}

/** 시장별 조건 */
export interface MarketCondition {
  market: string;
  accuracy: number;
  total: number;
  best_theme: string | null;
  worst_theme: string | null;
}

/** 전체 예측 컨텍스트 */
export interface PredictionContext {
  version: string;
  generated_at: string;
  analysis_days: number;
  total_predictions: number;
  overall_accuracy: number;
  direction_accuracy: DirectionAccuracy[];
  theme_predictability: ThemePredictability[];
  sentiment_ranges: SentimentRangeBucket[];
  news_count_effect: NewsCountEffect[];
  confidence_calibration: ConfidenceCalibration[];
  score_ranges: ScoreRangeBucket[];
  failure_patterns: FailurePattern[];
  market_conditions: MarketCondition[];
}

/** LLM 예측 응답 */
export interface LLMPredictionResponse {
  stock_code: string;
  stock_name: string | null;
  method: 'llm' | 'heuristic_fallback';
  direction: 'up' | 'down' | 'neutral';
  prediction_score: number;
  confidence: number;
  reasoning: string;
  heuristic_direction: string | null;
  heuristic_score: number | null;
  context_version: string | null;
  based_on_days: number | null;
}

/** 컨텍스트 리빌드 응답 */
export interface ContextRebuildResponse {
  success: boolean;
  version: string;
  analysis_days: number;
  total_predictions: number;
  overall_accuracy: number;
  file_path: string;
  generated_at: string;
}
