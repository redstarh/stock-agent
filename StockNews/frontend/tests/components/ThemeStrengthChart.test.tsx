import { render, screen } from '@testing-library/react';
import ThemeStrengthChart from '../../src/components/charts/ThemeStrengthChart';
import type { ThemeItem } from '../../src/types/theme';

// Recharts uses ResizeObserver internally
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

const data: ThemeItem[] = [
  { theme: 'AI', strength_score: 92.5, news_count: 45, sentiment_avg: 0.7, date: '2024-01-15', market: 'KR' },
  { theme: '반도체', strength_score: 88.3, news_count: 38, sentiment_avg: 0.6, date: '2024-01-15', market: 'KR' },
];

describe('ThemeStrengthChart', () => {
  it('shows empty message when no data', () => {
    render(<ThemeStrengthChart data={[]} />);
    expect(screen.getByText('테마 데이터가 없습니다')).toBeInTheDocument();
  });

  it('renders chart container when data is provided', () => {
    const { container } = render(<ThemeStrengthChart data={data} />);
    // ResponsiveContainer renders a div wrapper
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});
