import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import StockDetailPage from '../../src/pages/StockDetailPage';

// Recharts uses ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

function renderWithRoute(code: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/stocks/${code}`]}>
        <Routes>
          <Route path="/stocks/:code" element={<StockDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('StockDetailPage', () => {
  it('extracts stock code from URL params', () => {
    renderWithRoute('005930');
    // Page renders without crashing — code extracted
    expect(screen.getByText(/005930/)).toBeInTheDocument();
  });

  it('displays stock name and score after loading', async () => {
    renderWithRoute('005930');
    await waitFor(() => {
      expect(screen.getAllByText('삼성전자').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText('85.5').length).toBeGreaterThanOrEqual(1);
  });

  it('shows loading state initially', () => {
    renderWithRoute('005930');
    expect(screen.getByText('스코어 로딩 중...')).toBeInTheDocument();
  });

  it('renders score timeline chart after data loads', async () => {
    const { container } = renderWithRoute('005930');
    await waitFor(() => {
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });
});
