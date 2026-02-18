import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PredictionChart from '../../src/components/charts/PredictionChart';

describe('PredictionChart', () => {
  it('예측 점수 게이지 렌더링', () => {
    render(<PredictionChart score={72.5} direction="up" confidence={0.85} />);
    expect(screen.getByTestId('prediction-gauge')).toBeInTheDocument();
  });

  it('score 표시', () => {
    render(<PredictionChart score={72.5} direction="up" confidence={0.85} />);
    expect(screen.getByText('72.5')).toBeInTheDocument();
  });

  it('score > 60 → 녹색', () => {
    render(<PredictionChart score={75} direction="up" confidence={0.85} />);
    const gauge = screen.getByTestId('prediction-gauge');
    expect(gauge).toHaveClass('text-green-600');
  });

  it('score 40-60 → 노란색', () => {
    render(<PredictionChart score={50} direction="neutral" confidence={0.65} />);
    const gauge = screen.getByTestId('prediction-gauge');
    expect(gauge).toHaveClass('text-yellow-500');
  });

  it('score < 40 → 빨강', () => {
    render(<PredictionChart score={25} direction="down" confidence={0.72} />);
    const gauge = screen.getByTestId('prediction-gauge');
    expect(gauge).toHaveClass('text-red-600');
  });

  it('direction 텍스트 표시', () => {
    render(<PredictionChart score={72.5} direction="up" confidence={0.85} />);
    expect(screen.getByText('상승 예측')).toBeInTheDocument();
  });

  it('confidence 바 표시', () => {
    render(<PredictionChart score={72.5} direction="up" confidence={0.85} />);
    expect(screen.getByText('신뢰도: 85%')).toBeInTheDocument();
  });

  it('null score → 데이터 없음', () => {
    render(<PredictionChart score={null} direction={null} confidence={null} />);
    expect(screen.getByText('예측 데이터 없음')).toBeInTheDocument();
  });
});
