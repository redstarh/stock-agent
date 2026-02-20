import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TierStatus from '../../../src/components/ml/TierStatus';

describe('TierStatus', () => {
  it('shows all three tiers', () => {
    render(<TierStatus currentSamples={300} activeTier={1} />);
    expect(screen.getByText(/T1: Core/)).toBeInTheDocument();
    expect(screen.getByText(/T2: Extended/)).toBeInTheDocument();
    expect(screen.getByText(/T3: Advanced/)).toBeInTheDocument();
  });

  it('shows Active for the active tier', () => {
    render(<TierStatus currentSamples={300} activeTier={1} />);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('shows sample progress for locked tiers', () => {
    render(<TierStatus currentSamples={300} activeTier={1} />);
    expect(screen.getByText('300/1000')).toBeInTheDocument();
  });
});
