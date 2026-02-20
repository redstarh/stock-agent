import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { MarketProvider } from '../../../src/contexts/MarketContext';
import Layout from '../../../src/components/layout/Layout';
import type { Notification } from '../../../src/hooks/useWebSocket';

const defaultProps = {
  notifications: [] as Notification[],
  unreadCount: 0,
  onMarkAsRead: vi.fn(),
  onMarkAllAsRead: vi.fn(),
  onClearNotifications: vi.fn(),
};

describe('Layout', () => {
  it('renders children in main content area', () => {
    render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps}>
          <div data-testid="test-content">Test Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    expect(screen.getByTestId('test-content')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders Header component', () => {
    render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps}>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    expect(screen.getByRole('link', { name: 'StockNews' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '알림' })).toBeInTheDocument();
  });

  it('renders Sidebar component', () => {
    render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps}>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    // Check sidebar is present by looking for complementary role
    expect(screen.getByRole('complementary')).toBeInTheDocument();

    // Check that navigation items exist (multiple matches expected in Header + Sidebar)
    expect(screen.getAllByRole('link', { name: /Dashboard/ })).toHaveLength(2);
    expect(screen.getAllByRole('link', { name: /Theme Analysis/ })).toHaveLength(2);

    // Check MarketSelector is present
    expect(screen.getByRole('tablist')).toBeInTheDocument();
  });

  it('passes notifications to Header', () => {
    const notifications: Notification[] = [
      {
        id: '1',
        message: { type: 'breaking_news', data: { title: '속보: 삼성전자' } },
        timestamp: Date.now(),
        read: false,
      },
    ];

    render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps} notifications={notifications} unreadCount={1}>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('wraps content in proper layout structure', () => {
    const { container } = render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps}>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    // Check for main container structure
    const mainElement = container.querySelector('main');
    expect(mainElement).toBeInTheDocument();
    expect(mainElement).toHaveClass('flex-1', 'p-6');
  });

  it('has responsive flex layout', () => {
    const { container } = render(
      <MarketProvider>
      <MemoryRouter>
        <Layout {...defaultProps}>
          <div>Content</div>
        </Layout>
      </MemoryRouter>
      </MarketProvider>
    );

    const rootDiv = container.firstChild;
    expect(rootDiv).toHaveClass('flex', 'min-h-screen', 'bg-gray-50');
  });
});
