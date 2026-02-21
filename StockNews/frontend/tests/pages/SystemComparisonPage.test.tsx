import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeAll } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import SystemComparisonPage from '../../src/pages/SystemComparisonPage';
import { MarketProvider } from '../../src/contexts/MarketContext';

// Mock ResizeObserver for Recharts
beforeAll(() => {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MarketProvider>
        <MemoryRouter>
          {ui}
        </MemoryRouter>
      </MarketProvider>
    </QueryClientProvider>
  );
}

describe('SystemComparisonPage', () => {
  it('renders page title', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.getByText('Advan 예측 시뮬레이션 비교')).toBeInTheDocument();
  });

  it('renders subtitle description', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(
      screen.getByText('이벤트 기반 예측 정책별 시뮬레이션 결과 비교')
    ).toBeInTheDocument();
  });

  it('does not render period selection buttons', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.queryByText('7일')).not.toBeInTheDocument();
    expect(screen.queryByText('30일')).not.toBeInTheDocument();
    expect(screen.queryByText('90일')).not.toBeInTheDocument();
  });

  it('does not render date picker', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.queryByText('조회일:')).not.toBeInTheDocument();
  });

  it('hides Advan run selectors when no runs loaded', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.queryByText('Advan 실행:')).not.toBeInTheDocument();
    expect(screen.queryByText('비교 실행:')).not.toBeInTheDocument();
  });

  it('shows stock comparison section', async () => {
    renderWithProviders(<SystemComparisonPage />);
    await waitFor(() => {
      expect(screen.getByText('주가별 예측 비교')).toBeInTheDocument();
    });
  });

  it('shows theme comparison section', async () => {
    renderWithProviders(<SystemComparisonPage />);
    await waitFor(() => {
      expect(screen.getByText('테마별 예측 비교')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.getByText('데이터 로딩 중...')).toBeInTheDocument();
  });

  it('uses market context without errors', () => {
    renderWithProviders(<SystemComparisonPage />);
    expect(screen.getByText('Advan 예측 시뮬레이션 비교')).toBeInTheDocument();
  });
});
