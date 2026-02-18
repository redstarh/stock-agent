import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import Sidebar from '../../../src/components/layout/Sidebar';

describe('Sidebar', () => {
  it('renders navigation menu items', () => {
    render(
      <MemoryRouter>
        <Sidebar market="KR" onMarketChange={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /Dashboard/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Theme Analysis/ })).toBeInTheDocument();
  });

  it('highlights active route', () => {
    render(
      <MemoryRouter initialEntries={['/themes']}>
        <Sidebar market="KR" onMarketChange={() => {}} />
      </MemoryRouter>
    );

    const themeLink = screen.getByRole('link', { name: /Theme Analysis/ });
    expect(themeLink).toHaveClass('bg-blue-50', 'text-blue-600');
  });

  it('renders MarketSelector', () => {
    render(
      <MemoryRouter>
        <Sidebar market="KR" onMarketChange={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByRole('tablist')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'KR' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'US' })).toBeInTheDocument();
  });

  it('calls onMarketChange when market is changed', async () => {
    const user = userEvent.setup();
    const handleMarketChange = vi.fn();

    render(
      <MemoryRouter>
        <Sidebar market="KR" onMarketChange={handleMarketChange} />
      </MemoryRouter>
    );

    await user.click(screen.getByRole('tab', { name: 'US' }));
    expect(handleMarketChange).toHaveBeenCalledWith('US');
  });

  it('has hamburger menu button for mobile', () => {
    render(
      <MemoryRouter>
        <Sidebar market="KR" onMarketChange={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: 'Toggle menu' })).toBeInTheDocument();
  });

  it('toggles sidebar visibility on mobile menu click', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <Sidebar market="KR" onMarketChange={() => {}} />
      </MemoryRouter>
    );

    const toggleButton = screen.getByRole('button', { name: 'Toggle menu' });
    const sidebar = screen.getByRole('complementary');

    // Initially hidden on mobile (has -translate-x-full)
    expect(sidebar).toHaveClass('-translate-x-full');

    // Click to open
    await user.click(toggleButton);
    expect(sidebar).toHaveClass('translate-x-0');

    // Click to close
    await user.click(toggleButton);
    expect(sidebar).toHaveClass('-translate-x-full');
  });
});
