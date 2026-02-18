import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { describe, it, expect } from 'vitest';

// Helper: wrap with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

// Import after mocks are set up (MSW from setup.ts)
import { usePrediction } from '../../src/hooks/usePrediction';

describe('usePrediction', () => {
  it('종목코드로 예측 데이터 fetch', async () => {
    const { result } = renderHook(() => usePrediction('005930'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.stock_code).toBe('005930');
    expect(result.current.data?.prediction_score).toBe(72.5);
    expect(result.current.data?.direction).toBe('up');
    expect(result.current.data?.confidence).toBe(0.85);
  });

  it('에러 시 isError=true', async () => {
    const { result } = renderHook(() => usePrediction('INVALID'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('빈 종목코드 → enabled=false', () => {
    const { result } = renderHook(() => usePrediction(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.fetchStatus).toBe('idle');
  });
});
