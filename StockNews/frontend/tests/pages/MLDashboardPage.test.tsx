import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import MLDashboardPage from '../../src/pages/MLDashboardPage';

// Mock the hooks
vi.mock('../../src/contexts/MarketContext', () => ({
  useMarket: () => ({ market: 'KR', setMarket: vi.fn() }),
}));

vi.mock('../../src/hooks/useMLDashboard', () => ({
  useMLDashboard: () => ({
    stats: {
      total_records: 500,
      labeled_records: 400,
      markets: [
        { market: 'KR', total_records: 300, labeled_records: 250, accuracy: 62.5 },
        { market: 'US', total_records: 200, labeled_records: 150, accuracy: 58.0 },
      ],
    },
    models: [
      {
        id: 1,
        model_name: 'lightgbm_KR_t1',
        model_version: '1.0',
        model_type: 'lightgbm',
        market: 'KR',
        feature_tier: 1,
        feature_list: ['rsi_14', 'news_score'],
        train_accuracy: 0.65,
        test_accuracy: 0.62,
        cv_accuracy: 0.61,
        cv_std: 0.03,
        train_samples: 200,
        test_samples: 50,
        is_active: true,
        feature_importances: { rsi_14: 0.18, news_score: 0.15 },
        created_at: '2026-02-01T00:00:00Z',
      },
    ],
    activeModel: {
      id: 1,
      model_name: 'lightgbm_KR_t1',
      model_type: 'lightgbm',
      feature_tier: 1,
      feature_list: ['rsi_14', 'news_score'],
      cv_accuracy: 0.61,
      cv_std: 0.03,
      train_samples: 200,
      is_active: true,
      feature_importances: { rsi_14: 0.18, news_score: 0.15 },
    },
    isLoading: false,
    trainModel: vi.fn(),
    isTraining: false,
    activateModel: vi.fn(),
    evaluateModel: vi.fn(),
    isEvaluating: false,
    evaluateResult: null,
  }),
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MLDashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('MLDashboardPage', () => {
  it('renders page title', () => {
    renderPage();
    expect(screen.getByText('ML Model Dashboard')).toBeInTheDocument();
  });

  it('renders train button', () => {
    renderPage();
    expect(screen.getByText('Train New Model')).toBeInTheDocument();
  });

  it('renders evaluate button', () => {
    renderPage();
    expect(screen.getByText('Evaluate')).toBeInTheDocument();
  });

  it('renders active model info', () => {
    renderPage();
    expect(screen.getByText('LightGBM')).toBeInTheDocument();
    expect(screen.getByText('Active Model')).toBeInTheDocument();
  });

  it('renders model list', () => {
    renderPage();
    expect(screen.getByText('All Models')).toBeInTheDocument();
    expect(screen.getByText('lightgbm_KR_t1')).toBeInTheDocument();
  });

  it('renders tier status', () => {
    renderPage();
    expect(screen.getByText('Tier Status')).toBeInTheDocument();
  });

  it('renders accuracy trend chart section', () => {
    renderPage();
    expect(screen.getByText('Accuracy Trend')).toBeInTheDocument();
  });

  it('renders feature importance chart section', () => {
    renderPage();
    expect(screen.getByText('Feature Importance')).toBeInTheDocument();
  });
});
