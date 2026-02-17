import { render, screen } from '@testing-library/react';
import SentimentIndicator from '../../src/components/common/SentimentIndicator';

describe('SentimentIndicator', () => {
  it('renders positive as green badge with 긍정', () => {
    render(<SentimentIndicator sentiment="positive" />);
    const badge = screen.getByText('긍정');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveStyle({ backgroundColor: '#22c55e' });
  });

  it('renders negative as red badge with 부정', () => {
    render(<SentimentIndicator sentiment="negative" />);
    const badge = screen.getByText('부정');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveStyle({ backgroundColor: '#ef4444' });
  });

  it('renders neutral as gray badge with 중립', () => {
    render(<SentimentIndicator sentiment="neutral" />);
    const badge = screen.getByText('중립');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveStyle({ backgroundColor: '#6b7280' });
  });

  it('displays numeric value when provided', () => {
    render(<SentimentIndicator sentiment="positive" value={0.7} />);
    expect(screen.getByText('0.7')).toBeInTheDocument();
  });
});
