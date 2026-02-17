import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';

// Helper: wrap with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

// Import after mocks are set up (MSW from setup.ts)
import { useNewsScore } from '../../src/hooks/useNewsScore';

describe('useNewsScore', () => {
  it('fetches score data for a stock code', async () => {
    const { result } = renderHook(() => useNewsScore('005930'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.score.isSuccess).toBe(true));
    expect(result.current.score.data?.stock_code).toBe('005930');
    expect(result.current.score.data?.news_score).toBe(85.5);
  });

  it('fetches timeline data for a stock code', async () => {
    const { result } = renderHook(() => useNewsScore('005930'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.timeline.isSuccess).toBe(true));
    expect(result.current.timeline.data).toHaveLength(7);
    expect(result.current.timeline.data?.[0]).toHaveProperty('date');
    expect(result.current.timeline.data?.[0]).toHaveProperty('score');
  });
});
