import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AccuracyOverviewCard from '../../../src/components/verification/AccuracyOverviewCard';
import type { AccuracyResponse } from '../../../src/types/verification';

const mockAccuracyData: AccuracyResponse = {
  period_days: 30,
  market: 'KR',
  overall_accuracy: 75.5,
  total_predictions: 100,
  correct_predictions: 75,
  by_direction: {
    up: { total: 40, correct: 32, accuracy: 80.0 },
    down: { total: 35, correct: 28, accuracy: 80.0 },
    neutral: { total: 25, correct: 15, accuracy: 60.0 },
  },
  daily_trend: [
    { date: '2024-01-10', accuracy: 70.0, total: 10 },
    { date: '2024-01-11', accuracy: 75.0, total: 12 },
  ],
};

describe('AccuracyOverviewCard', () => {
  it('renders empty state when no data provided', () => {
    render(<AccuracyOverviewCard />);
    expect(screen.getByText('데이터가 없습니다')).toBeInTheDocument();
  });

  it('displays overall accuracy percentage', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('75.5%')).toBeInTheDocument();
  });

  it('displays total predictions count', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('100건')).toBeInTheDocument();
  });

  it('displays correct predictions count', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('75건')).toBeInTheDocument();
  });

  it('calculates and displays incorrect predictions count', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('25건')).toBeInTheDocument();
  });

  it('displays direction breakdown for up predictions', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('상승 예측')).toBeInTheDocument();
    expect(screen.getByText('32/40')).toBeInTheDocument();
    const accuracyElements = screen.getAllByText('80.0%');
    expect(accuracyElements.length).toBeGreaterThan(0);
  });

  it('displays direction breakdown for down predictions', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('하락 예측')).toBeInTheDocument();
    expect(screen.getByText('28/35')).toBeInTheDocument();
    const accuracyElements = screen.getAllByText('80.0%');
    expect(accuracyElements.length).toBeGreaterThan(0);
  });

  it('displays direction breakdown for neutral predictions', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    expect(screen.getByText('중립 예측')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
    expect(screen.getByText('15/25')).toBeInTheDocument();
  });

  it('applies green color for high accuracy (>= 70%)', () => {
    render(<AccuracyOverviewCard data={mockAccuracyData} />);
    const accuracyElement = screen.getByText('75.5%');
    expect(accuracyElement).toHaveClass('text-green-600');
  });

  it('applies yellow color for medium accuracy (50-69%)', () => {
    const mediumAccuracyData = { ...mockAccuracyData, overall_accuracy: 55.0 };
    render(<AccuracyOverviewCard data={mediumAccuracyData} />);
    const accuracyElement = screen.getByText('55.0%');
    expect(accuracyElement).toHaveClass('text-yellow-600');
  });

  it('applies red color for low accuracy (< 50%)', () => {
    const lowAccuracyData = { ...mockAccuracyData, overall_accuracy: 45.0 };
    render(<AccuracyOverviewCard data={lowAccuracyData} />);
    const accuracyElement = screen.getByText('45.0%');
    expect(accuracyElement).toHaveClass('text-red-600');
  });

  it('handles zero accuracy gracefully', () => {
    const zeroAccuracyData = { ...mockAccuracyData, overall_accuracy: 0 };
    render(<AccuracyOverviewCard data={zeroAccuracyData} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('handles null overall_accuracy by defaulting to 0', () => {
    const nullAccuracyData = { ...mockAccuracyData, overall_accuracy: null };
    render(<AccuracyOverviewCard data={nullAccuracyData} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });
});
