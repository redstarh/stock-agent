import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ThemeAnalysisPage from '../../src/pages/ThemeAnalysisPage';

// Recharts uses ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ThemeAnalysisPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ThemeAnalysisPage', () => {
  it('renders page heading', () => {
    renderWithProviders();
    expect(screen.getByText('테마 분석')).toBeInTheDocument();
  });

  it('renders market selector', () => {
    renderWithProviders();
    expect(screen.getByRole('tablist')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    renderWithProviders();
    expect(screen.getByText('테마 로딩 중...')).toBeInTheDocument();
  });

  it('renders theme chart after data loads', async () => {
    const { container } = renderWithProviders();
    await waitFor(() => {
      expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
    });
  });

  it('displays theme data sorted by strength', async () => {
    renderWithProviders();
    await waitFor(() => {
      // MSW returns AI (92.5), 반도체 (88.3), 2차전지 (65.1)
      expect(screen.getByText('AI')).toBeInTheDocument();
      expect(screen.getByText('반도체')).toBeInTheDocument();
      expect(screen.getByText('2차전지')).toBeInTheDocument();
    });
  });
});
