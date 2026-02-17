import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MarketSelector from '../../src/components/common/MarketSelector';

describe('MarketSelector', () => {
  it('renders KR and US tabs', () => {
    render(<MarketSelector selected="KR" onChange={() => {}} />);
    expect(screen.getByRole('tab', { name: 'KR' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'US' })).toBeInTheDocument();
  });

  it('marks selected tab with aria-selected', () => {
    render(<MarketSelector selected="KR" onChange={() => {}} />);
    expect(screen.getByRole('tab', { name: 'KR' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'US' })).toHaveAttribute('aria-selected', 'false');
  });

  it('calls onChange when clicking a tab', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<MarketSelector selected="KR" onChange={handleChange} />);

    await user.click(screen.getByRole('tab', { name: 'US' }));
    expect(handleChange).toHaveBeenCalledWith('US');
  });

  it('has tablist role on container', () => {
    render(<MarketSelector selected="KR" onChange={() => {}} />);
    expect(screen.getByRole('tablist')).toBeInTheDocument();
  });
});
