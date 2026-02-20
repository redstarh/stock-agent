import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ModelCard from '../../../src/components/ml/ModelCard';

describe('ModelCard', () => {
  it('shows empty state when no model', () => {
    render(<ModelCard model={null} />);
    expect(screen.getByText('No active model')).toBeInTheDocument();
  });

  it('shows model details when provided', () => {
    const model = {
      id: 1,
      model_name: 'lgb_kr_t1',
      model_version: '1.0',
      model_type: 'lightgbm' as const,
      market: 'KR',
      feature_tier: 1,
      feature_list: ['rsi_14', 'news_score', 'sentiment_score'],
      train_accuracy: 0.65,
      test_accuracy: 0.62,
      cv_accuracy: 0.61,
      cv_std: 0.03,
      train_samples: 250,
      test_samples: 50,
      is_active: true,
      feature_importances: null,
      created_at: '2026-02-01T00:00:00Z',
    };

    render(<ModelCard model={model} />);
    expect(screen.getByText('LightGBM')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText(/61\.0% CV accuracy/)).toBeInTheDocument();
  });
});
