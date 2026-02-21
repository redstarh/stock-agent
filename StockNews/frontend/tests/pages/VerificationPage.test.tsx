import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import VerificationPage from '../../src/pages/VerificationPage';
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

describe('VerificationPage', () => {
  it('renders page title', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.getByText('예측 검증 (Advan)')).toBeInTheDocument();
  });

  it('renders run selector label', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.getByText('시뮬레이션 실행')).toBeInTheDocument();
  });

  it('renders run selector dropdown', () => {
    renderWithProviders(<VerificationPage />);
    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  it('does not render date picker or days selector', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.queryByText('조회일')).not.toBeInTheDocument();
    expect(screen.queryByText('기간')).not.toBeInTheDocument();
    expect(screen.queryByRole('option', { name: '7일' })).not.toBeInTheDocument();
    expect(screen.queryByRole('option', { name: '30일' })).not.toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.getByText('검증 데이터 로딩 중...')).toBeInTheDocument();
  });

  it('renders stock results section header', async () => {
    renderWithProviders(<VerificationPage />);
    await waitFor(() => {
      expect(screen.getByText(/종목별 검증 결과/)).toBeInTheDocument();
    });
  });

  it('renders theme accuracy section header', async () => {
    renderWithProviders(<VerificationPage />);
    await waitFor(() => {
      expect(screen.getByText('테마별 정확도')).toBeInTheDocument();
    });
  });

  it('renders grid layout for stock and theme sections', async () => {
    const { container } = renderWithProviders(<VerificationPage />);
    await waitFor(() => {
      const gridContainer = container.querySelector('.grid.grid-cols-1.gap-6.lg\\:grid-cols-2');
      expect(gridContainer).toBeInTheDocument();
    });
  });
});
