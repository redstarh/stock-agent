import { render, screen } from '@testing-library/react';
import SentimentPie from '../../src/components/charts/SentimentPie';

// Recharts uses ResizeObserver
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

describe('SentimentPie', () => {
  it('renders chart when counts are provided', () => {
    const { container } = render(
      <SentimentPie positive={5} neutral={3} negative={2} />,
    );
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('shows empty message when all counts are zero', () => {
    render(<SentimentPie positive={0} neutral={0} negative={0} />);
    expect(screen.getByText('감성 데이터가 없습니다')).toBeInTheDocument();
  });
});
