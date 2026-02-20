import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';
import DailyAccuracyChart from '../../../src/components/verification/DailyAccuracyChart';
import type { DailyTrend } from '../../../src/types/verification';

// Mock ResizeObserver for Recharts
beforeAll(() => {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockDailyTrend: DailyTrend[] = [
  { date: '2024-01-10', accuracy: 70.0, total: 10 },
  { date: '2024-01-11', accuracy: 75.0, total: 12 },
  { date: '2024-01-12', accuracy: 80.0, total: 15 },
  { date: '2024-01-13', accuracy: 72.5, total: 14 },
  { date: '2024-01-14', accuracy: 78.0, total: 13 },
];

describe('DailyAccuracyChart', () => {
  it('renders empty state when no data provided', () => {
    render(<DailyAccuracyChart data={[]} />);
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument();
  });

  it('renders chart container when data is provided', () => {
    const { container } = render(<DailyAccuracyChart data={mockDailyTrend} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('renders with proper wrapper styling', () => {
    const { container } = render(<DailyAccuracyChart data={mockDailyTrend} />);
    const wrapper = container.querySelector('.rounded-lg.border.bg-white.p-4');
    expect(wrapper).toBeInTheDocument();
  });

  it('renders chart with wrapper elements', () => {
    const { container } = render(<DailyAccuracyChart data={mockDailyTrend} />);
    const chartWrapper = container.querySelector('.recharts-responsive-container');
    expect(chartWrapper).toBeTruthy();
    expect(chartWrapper).toBeInTheDocument();
  });

  it('handles single data point', () => {
    const singlePoint = [mockDailyTrend[0]];
    const { container } = render(<DailyAccuracyChart data={singlePoint} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('handles undefined data gracefully', () => {
    render(<DailyAccuracyChart data={undefined as any} />);
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument();
  });

  it('renders with fixed height container', () => {
    const { container } = render(<DailyAccuracyChart data={mockDailyTrend} />);
    const responsiveContainer = container.querySelector('.recharts-responsive-container');
    expect(responsiveContainer).toHaveStyle({ width: '100%', height: '300px' });
  });
});
