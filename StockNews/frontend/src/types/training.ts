/** ML Training data types. */

export interface MLModel {
  id: number;
  model_name: string;
  model_version: string;
  model_type: 'lightgbm' | 'random_forest';
  market: string;
  feature_tier: number;
  feature_list: string[];
  train_accuracy: number | null;
  test_accuracy: number | null;
  cv_accuracy: number | null;
  cv_std: number | null;
  train_samples: number | null;
  test_samples: number | null;
  is_active: boolean;
  feature_importances: Record<string, number> | null;
  created_at: string | null;
}

export interface TrainingStats {
  total_records: number;
  labeled_records: number;
  markets: MarketStats[];
}

export interface MarketStats {
  market: string;
  total_records: number;
  labeled_records: number;
  accuracy: number | null;
  date_range_start: string | null;
  date_range_end: string | null;
}

export interface TrainResult {
  status: 'trained' | 'insufficient_data';
  model_id?: number;
  model_type?: string;
  market?: string;
  feature_tier?: number;
  train_accuracy?: number;
  test_accuracy?: number | null;
  cv_accuracy?: number;
  cv_std?: number;
  samples?: number;
  features?: number;
  required?: number;
}

export interface EvaluateResult {
  status: 'evaluated' | 'no_active_model' | 'no_data';
  model_id?: number;
  model_name?: string;
  market?: string;
  accuracy?: number;
  precision?: Record<string, number>;
  recall?: Record<string, number>;
  f1?: Record<string, number>;
  confusion_matrix?: number[][];
  labels?: string[];
}

export interface TierStatus {
  tier: number;
  features: number;
  min_samples: number;
  current_samples: number;
  status: 'active' | 'ready' | 'locked';
}
