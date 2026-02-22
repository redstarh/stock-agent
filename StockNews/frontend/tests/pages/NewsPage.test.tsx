import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { MarketProvider } from '../../src/contexts/MarketContext';
import NewsPage from '../../src/pages/NewsPage';

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
          <NewsPage />
        </MemoryRouter>
      </MarketProvider>
    </QueryClientProvider>,
  );
}

describe('NewsPage', () => {
  it('renders page heading', () => {
    renderWithProviders();
    expect(screen.getByText('최신 뉴스')).toBeInTheDocument();
  });

  it('renders manual collect section', () => {
    renderWithProviders();
    expect(screen.getByText('수동 수집')).toBeInTheDocument();
  });

  it('renders stock name input', () => {
    renderWithProviders();
    expect(screen.getByPlaceholderText('종목명')).toBeInTheDocument();
  });

  it('renders stock code input', () => {
    renderWithProviders();
    expect(screen.getByPlaceholderText('종목코드')).toBeInTheDocument();
  });

  it('renders add to scope checkbox', () => {
    renderWithProviders();
    expect(screen.getByText('일일 수집에 추가')).toBeInTheDocument();
  });

  it('renders collect button', () => {
    renderWithProviders();
    expect(screen.getByText('수집')).toBeInTheDocument();
  });

  it('disables collect button when inputs are empty', () => {
    renderWithProviders();
    const button = screen.getByText('수집');
    expect(button).toBeDisabled();
  });

  it('enables collect button when both inputs have values', () => {
    renderWithProviders();
    const nameInput = screen.getByPlaceholderText('종목명');
    const codeInput = screen.getByPlaceholderText('종목코드');

    fireEvent.change(nameInput, { target: { value: '삼성전자' } });
    fireEvent.change(codeInput, { target: { value: '005930' } });

    const button = screen.getByText('수집');
    expect(button).not.toBeDisabled();
  });

  it('renders filter panel', () => {
    renderWithProviders();
    // FilterPanel should render search/filter controls
    expect(screen.getByText('검색 결과')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    renderWithProviders();
    expect(screen.getByText('뉴스 로딩 중...')).toBeInTheDocument();
  });

  it('loads and displays news from MSW', async () => {
    renderWithProviders();
    await waitFor(() => {
      // MSW returns mock news data
      expect(screen.queryByText('뉴스 로딩 중...')).not.toBeInTheDocument();
    });
  });
});
