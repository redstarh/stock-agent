import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeAll } from 'vitest';
import ThemeAccuracyBreakdown from '../../../src/components/verification/ThemeAccuracyBreakdown';
import type { ThemeAccuracy } from '../../../src/types/verification';

// Mock ResizeObserver for Recharts
beforeAll(() => {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

const mockThemes: ThemeAccuracy[] = [
  {
    theme: 'AI',
    market: 'KR',
    total_stocks: 15,
    correct_count: 12,
    accuracy_rate: 80.0,
    avg_predicted_score: 75.5,
    avg_actual_change_pct: 2.5,
    rise_index: 70.0,
  },
  {
    theme: '반도체',
    market: 'KR',
    total_stocks: 20,
    correct_count: 14,
    accuracy_rate: 70.0,
    avg_predicted_score: 72.3,
    avg_actual_change_pct: 1.8,
    rise_index: 65.0,
  },
  {
    theme: '2차전지',
    market: 'KR',
    total_stocks: 12,
    correct_count: 5,
    accuracy_rate: 41.7,
    avg_predicted_score: 60.0,
    avg_actual_change_pct: -0.5,
    rise_index: 45.0,
  },
  {
    theme: '바이오',
    market: 'KR',
    total_stocks: 18,
    correct_count: 11,
    accuracy_rate: 61.1,
    avg_predicted_score: 68.0,
    avg_actual_change_pct: 1.2,
    rise_index: 55.0,
  },
  {
    theme: '게임',
    market: 'KR',
    total_stocks: 10,
    correct_count: 7,
    accuracy_rate: 70.0,
    avg_predicted_score: 70.5,
    avg_actual_change_pct: 1.5,
    rise_index: 60.0,
  },
  {
    theme: '클라우드',
    market: 'KR',
    total_stocks: 8,
    correct_count: 6,
    accuracy_rate: 75.0,
    avg_predicted_score: 73.0,
    avg_actual_change_pct: 2.0,
    rise_index: 68.0,
  },
];

describe('ThemeAccuracyBreakdown', () => {
  it('renders empty state when no themes provided', () => {
    render(<ThemeAccuracyBreakdown themes={[]} />);
    expect(screen.getByText('테마 데이터가 없습니다')).toBeInTheDocument();
  });

  it('renders chart container', () => {
    const { container } = render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('displays top 5 themes in the list', () => {
    render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    expect(screen.getByText('AI')).toBeInTheDocument();
    expect(screen.getByText('클라우드')).toBeInTheDocument();
    expect(screen.getByText('반도체')).toBeInTheDocument();
    expect(screen.getByText('게임')).toBeInTheDocument();
    expect(screen.getByText('바이오')).toBeInTheDocument();
  });

  it('displays theme accuracy percentages', () => {
    render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    const accuracyElements = screen.getAllByText(/\d+\.\d+%/);
    expect(accuracyElements.length).toBeGreaterThan(0);
    expect(screen.getByText('80.0%')).toBeInTheDocument();
  });

  it('displays total stocks count for each theme', () => {
    render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    expect(screen.getByText('15종목')).toBeInTheDocument();
    expect(screen.getByText('20종목')).toBeInTheDocument();
  });

  it('sorts themes by accuracy in descending order', () => {
    render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    const themeElements = screen.getAllByText(/종목$/);
    // First should be AI (80.0%) with 15 stocks
    expect(themeElements[0].textContent).toBe('15종목');
  });

  it('handles single theme correctly', () => {
    const singleTheme = [mockThemes[0]];
    render(<ThemeAccuracyBreakdown themes={singleTheme} />);
    expect(screen.getByText('AI')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
  });

  it('renders with rounded border styling', () => {
    const { container } = render(<ThemeAccuracyBreakdown themes={mockThemes} />);
    const wrapper = container.querySelector('.rounded-lg.border.bg-white');
    expect(wrapper).toBeInTheDocument();
  });
});
