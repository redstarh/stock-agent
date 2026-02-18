import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PredictionSignal from '../../src/components/common/PredictionSignal';

describe('PredictionSignal', () => {
  it('direction=up → 상승 표시 + 녹색', () => {
    render(<PredictionSignal direction="up" confidence={0.85} />);
    const signal = screen.getByTestId('prediction-signal');
    expect(signal).toHaveTextContent('▲ 상승');
    expect(signal).toHaveClass('bg-green-500');
  });

  it('direction=down → 하락 표시 + 빨강', () => {
    render(<PredictionSignal direction="down" confidence={0.72} />);
    const signal = screen.getByTestId('prediction-signal');
    expect(signal).toHaveTextContent('▼ 하락');
    expect(signal).toHaveClass('bg-red-500');
  });

  it('direction=neutral → 중립 표시', () => {
    render(<PredictionSignal direction="neutral" confidence={0.65} />);
    const signal = screen.getByTestId('prediction-signal');
    expect(signal).toHaveTextContent('— 중립');
    expect(signal).toHaveClass('bg-gray-400');
  });

  it('null direction → 예측 없음', () => {
    render(<PredictionSignal direction={null} confidence={null} />);
    expect(screen.getByText('예측 없음')).toBeInTheDocument();
  });

  it('confidence 표시', () => {
    render(<PredictionSignal direction="up" confidence={0.85} />);
    expect(screen.getByText('신뢰도: 85%')).toBeInTheDocument();
  });

  it('null confidence → 신뢰도 미표시', () => {
    render(<PredictionSignal direction="up" confidence={null} />);
    expect(screen.queryByText(/신뢰도/)).not.toBeInTheDocument();
  });
});
