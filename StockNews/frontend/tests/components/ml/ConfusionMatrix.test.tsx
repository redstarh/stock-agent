import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ConfusionMatrix from '../../../src/components/ml/ConfusionMatrix';

describe('ConfusionMatrix', () => {
  it('shows empty state with no data', () => {
    render(<ConfusionMatrix matrix={null} labels={null} />);
    expect(screen.getByText('No evaluation data')).toBeInTheDocument();
  });

  it('renders matrix cells', () => {
    const matrix = [[42, 8], [10, 38]];
    const labels = ['up', 'down'];

    render(<ConfusionMatrix matrix={matrix} labels={labels} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('38')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});
