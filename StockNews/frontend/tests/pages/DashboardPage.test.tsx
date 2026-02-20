import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { MarketProvider } from '../../src/contexts/MarketContext';
import DashboardPage from '../../src/pages/DashboardPage';

// Recharts uses ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MarketProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </MarketProvider>
    </QueryClientProvider>,
  );
}

describe('DashboardPage', () => {
  it('renders dashboard heading', () => {
    renderWithProviders();
    expect(screen.getByText('대시보드')).toBeInTheDocument();
  });

  it('renders section headings', () => {
    renderWithProviders();
    expect(screen.getByText('Top 종목')).toBeInTheDocument();
    expect(screen.getByText('테마 강도')).toBeInTheDocument();
  });

  it('shows loading states initially', () => {
    renderWithProviders();
    expect(screen.getByText('Top 종목 로딩 중...')).toBeInTheDocument();
    expect(screen.getByText('테마 로딩 중...')).toBeInTheDocument();
  });

  it('loads and displays top stock data from MSW', async () => {
    renderWithProviders();
    await waitFor(() => {
      expect(screen.getAllByText('삼성전자').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText('SK하이닉스').length).toBeGreaterThanOrEqual(1);
  });

  it('loads and displays theme chart from MSW', async () => {
    renderWithProviders();
    await waitFor(() => {
      // Chart renders — no empty state message
      expect(screen.queryByText('테마 데이터가 없습니다')).not.toBeInTheDocument();
    });
  });
});
