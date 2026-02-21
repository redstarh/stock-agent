/** Advan Simulation 관련 타입 정의 */

// ─── Event Types ───

export interface AdvanEvent {
  id: number;
  source_news_id: number | null;
  ticker: string;
  stock_name: string | null;
  market: string;
  event_type: string;
  direction: string;
  magnitude: number;
  magnitude_detail: string | null;
  novelty: number;
  credibility: number;
  is_disclosure: boolean;
  title: string;
  summary: string | null;
  source: string;
  confounders: string | null;
  event_timestamp: string;
  is_after_market: boolean;
  created_at: string;
}

export interface AdvanEventListResponse {
  events: AdvanEvent[];
  total: number;
}

export interface EventExtractRequest {
  market: string;
  date_from?: string | null;
  date_to?: string | null;
  force_rebuild: boolean;
}

export interface EventExtractResponse {
  extracted_count: number;
  skipped_count: number;
  error_count: number;
  message: string;
}

// ─── Policy Types ───

export interface EventPriors {
  실적: number;
  가이던스: number;
  수주: number;
  증자: number;
  소송: number;
  규제: number;
  경영권: number;
  자사주: number;
  배당: number;
  공급계약: number;
  기타: number;
}

export interface PolicyThresholds {
  buy_p: number;
  sell_p: number;
  abstain_low: number;
  abstain_high: number;
  label_threshold_pct: number;
  stop_loss_pct: number;
}

export interface TemplateConfig {
  include_features: boolean;
  include_similar_events: boolean;
  include_confounders: boolean;
  max_events_per_stock: number;
}

export interface RetrievalConfig {
  max_results: number;
  lookback_days: number;
  same_sector_only: boolean;
  similarity_threshold: number;
}

export interface AdvanPolicy {
  id: number;
  name: string;
  version: string;
  description: string | null;
  is_active: boolean;
  event_priors: EventPriors;
  thresholds: PolicyThresholds;
  template_config: TemplateConfig;
  retrieval_config: RetrievalConfig;
  latest_brier: number | null;
  latest_accuracy: number | null;
  latest_calibration: number | null;
  created_at: string;
  updated_at: string;
}

export interface AdvanPolicyListItem {
  id: number;
  name: string;
  version: string;
  description: string | null;
  is_active: boolean;
  latest_brier: number | null;
  latest_accuracy: number | null;
  latest_calibration: number | null;
  created_at: string;
}

export interface AdvanPolicyCreate {
  name: string;
  version?: string;
  description?: string | null;
  event_priors?: EventPriors;
  thresholds?: PolicyThresholds;
  template_config?: TemplateConfig;
  retrieval_config?: RetrievalConfig;
}

export interface AdvanPolicyUpdate {
  name?: string;
  version?: string;
  description?: string | null;
  is_active?: boolean;
  event_priors?: EventPriors;
  thresholds?: PolicyThresholds;
  template_config?: TemplateConfig;
  retrieval_config?: RetrievalConfig;
}

// ─── Prediction Types ───

export interface PredictionDriver {
  feature: string;
  sign: string;
  weight: number;
  evidence: string;
}

export interface AdvanPrediction {
  id: number;
  run_id: number;
  event_id: number | null;
  policy_id: number;
  ticker: string;
  prediction_date: string;
  horizon: number;
  prediction: string;
  p_up: number;
  p_down: number;
  p_flat: number;
  trade_action: string;
  position_size: number;
  top_drivers: PredictionDriver[] | null;
  invalidators: string[] | null;
  reasoning: string | null;
}

// ─── Label Types ───

export interface AdvanLabel {
  id: number;
  prediction_id: number;
  ticker: string;
  prediction_date: string;
  horizon: number;
  realized_ret: number | null;
  excess_ret: number | null;
  label: string | null;
  is_correct: boolean | null;
  label_date: string | null;
}

// ─── Simulation Run Types ───

export interface AdvanSimulationRun {
  id: number;
  name: string;
  policy_id: number;
  market: string;
  horizon: number;
  label_threshold_pct: number;
  date_from: string;
  date_to: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_predictions: number;
  correct_count: number;
  abstain_count: number;
  accuracy_rate: number;
  brier_score: number | null;
  calibration_error: number | null;
  auc_score: number | null;
  f1_score: number | null;
  avg_excess_return: number | null;
  by_event_type_metrics: Record<string, any> | null;
  duration_seconds: number;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AdvanSimulationRunCreate {
  name: string;
  policy_id: number;
  market?: string;
  horizon?: number;
  label_threshold_pct?: number;
  date_from: string;
  date_to: string;
}

export interface DirectionStat {
  total: number;
  correct: number;
  accuracy: number;
}

export interface AdvanSimulationRunDetail {
  run: AdvanSimulationRun;
  predictions: AdvanPrediction[];
  labels: AdvanLabel[];
  direction_stats: Record<string, DirectionStat>;
}

// ─── Compare Types ───

export interface AdvanCompareItem {
  id: number;
  name: string;
  policy_id: number;
  policy_name: string | null;
  market: string;
  horizon: number;
  date_from: string;
  date_to: string;
  total_predictions: number;
  correct_count: number;
  abstain_count: number;
  accuracy_rate: number;
  brier_score: number | null;
  calibration_error: number | null;
  auc_score: number | null;
  f1_score: number | null;
  avg_excess_return: number | null;
  by_event_type_metrics: Record<string, any> | null;
}

export interface AdvanCompareResponse {
  runs: AdvanCompareItem[];
}

// ─── Evaluation Types ───

export interface AdvanEvalMetrics {
  accuracy: number;
  f1: number;
  brier: number;
  calibration_error: number;
  auc: number | null;
  avg_excess_return: number | null;
  total_predictions: number;
  abstain_rate: number;
  by_event_type: Record<string, any> | null;
  by_direction: Record<string, any> | null;
  robustness_metrics: Record<string, any> | null;
}

export interface AdvanEvalRunResponse {
  id: number;
  policy_id: number;
  simulation_run_id: number | null;
  eval_period_from: string;
  eval_period_to: string;
  split_type: string;
  metrics: AdvanEvalMetrics;
  created_at: string;
}

// ─── Optimizer Types ───

export interface OptimizeRequest {
  base_policy_id: number;
  market?: string;
  date_from: string;
  date_to: string;
  num_candidates?: number;
  val_split_ratio?: number;
  target_metric?: string;
}

export interface OptimizeResponse {
  best_policy_id: number;
  best_policy_name: string;
  candidates_evaluated: number;
  best_metrics: AdvanEvalMetrics;
  improvement_pct: number;
  message: string;
}
