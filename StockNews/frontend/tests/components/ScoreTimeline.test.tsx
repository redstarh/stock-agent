import { render, screen } from '@testing-library/react';
import ScoreTimeline from '../../src/components/charts/ScoreTimeline';
import type { TimelinePoint } from '../../src/types/news';

// Recharts uses ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

const data: TimelinePoint[] = [
  { date: '2024-01-09', score: 60.2 },
  { date: '2024-01-10', score: 65.1 },
  { date: '2024-01-11', score: 70.3 },
  { date: '2024-01-12', score: 68.5 },
  { date: '2024-01-13', score: 75.2 },
  { date: '2024-01-14', score: 80.1 },
  { date: '2024-01-15', score: 85.5 },
];

describe('ScoreTimeline', () => {
  it('renders chart container when data is provided', () => {
    const { container } = render(<ScoreTimeline data={data} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('shows empty message when no data', () => {
    render(<ScoreTimeline data={[]} />);
    expect(screen.getByText('타임라인 데이터가 없습니다')).toBeInTheDocument();
  });

  it('renders with 7 data points', () => {
    const { container } = render(<ScoreTimeline data={data} />);
    // Chart should render without error
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});
