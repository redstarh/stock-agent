import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { useThemeStrength } from '../../src/hooks/useThemeStrength';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('useThemeStrength', () => {
  it('fetches theme data for a market', async () => {
    const { result } = renderHook(() => useThemeStrength('KR'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(3);
    expect(result.current.data?.[0]).toHaveProperty('theme');
    expect(result.current.data?.[0]).toHaveProperty('strength_score');
  });
});
