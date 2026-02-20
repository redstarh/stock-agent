import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    expect(screen.getByText('예측 검증')).toBeInTheDocument();
  });

  it('renders date input control', () => {
    renderWithProviders(<VerificationPage />);
    const dateInput = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    expect(dateInput).toBeInTheDocument();
  });

  it('renders days selector with default value', () => {
    renderWithProviders(<VerificationPage />);
    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('30');
  });

  it('shows loading state initially', () => {
    renderWithProviders(<VerificationPage />);
    expect(screen.getByText('검증 데이터 로딩 중...')).toBeInTheDocument();
  });

  it('renders AccuracyOverviewCard after loading', async () => {
    renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText('전체 정확도')).toBeInTheDocument();
    });
  });

  it('renders daily accuracy trend section', async () => {
    renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText('일별 정확도 추세')).toBeInTheDocument();
    });
  });

  it('renders stock results section', async () => {
    renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText(/종목별 검증 결과/)).toBeInTheDocument();
    });
  });

  it('renders theme accuracy section', async () => {
    renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText('테마별 정확도')).toBeInTheDocument();
    });
  });

  it('allows changing date selection', async () => {
    const user = userEvent.setup();
    renderWithProviders(<VerificationPage />);

    const dateInput = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    await user.clear(dateInput);
    await user.type(dateInput, '2024-01-15');

    expect(dateInput).toHaveValue('2024-01-15');
  });

  it('allows changing days period', async () => {
    const user = userEvent.setup();
    renderWithProviders(<VerificationPage />);

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '7');

    expect(select).toHaveValue('7');
  });

  it('displays 7, 30, and 90 days options', () => {
    renderWithProviders(<VerificationPage />);

    expect(screen.getByRole('option', { name: '7일' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '30일' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: '90일' })).toBeInTheDocument();
  });

  it('renders grid layout for stock results and theme sections', async () => {
    const { container } = renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText('전체 정확도')).toBeInTheDocument();
    });

    const gridContainer = container.querySelector('.grid.grid-cols-1.gap-6.lg\\:grid-cols-2');
    expect(gridContainer).toBeInTheDocument();
  });

  it('shows results count in stock results section header', async () => {
    renderWithProviders(<VerificationPage />);

    await waitFor(() => {
      expect(screen.getByText(/\(\d+건\)/)).toBeInTheDocument();
    });
  });
});
