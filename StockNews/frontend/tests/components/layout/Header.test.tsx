import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import Header from '../../../src/components/layout/Header';
import type { Notification } from '../../../src/hooks/useWebSocket';

const defaultProps = {
  notifications: [] as Notification[],
  unreadCount: 0,
  onMarkAsRead: vi.fn(),
  onMarkAllAsRead: vi.fn(),
  onClearNotifications: vi.fn(),
};

describe('Header', () => {
  it('renders app title with link to home', () => {
    render(
      <MemoryRouter>
        <Header {...defaultProps} />
      </MemoryRouter>
    );

    const titleLink = screen.getByRole('link', { name: 'StockNews' });
    expect(titleLink).toBeInTheDocument();
    expect(titleLink).toHaveAttribute('href', '/');
  });

  it('renders navigation links', () => {
    render(
      <MemoryRouter>
        <Header {...defaultProps} />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Theme Analysis' })).toBeInTheDocument();
  });

  it('renders NotificationBell component', () => {
    render(
      <MemoryRouter>
        <Header {...defaultProps} />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: '알림' })).toBeInTheDocument();
  });

  it('passes notifications to NotificationBell', () => {
    const notifications: Notification[] = [
      {
        id: '1',
        message: { type: 'breaking_news', data: { title: '속보: 삼성전자' } },
        timestamp: Date.now(),
        read: false,
      },
      {
        id: '2',
        message: { type: 'breaking_news', data: { title: '속보: SK하이닉스' } },
        timestamp: Date.now(),
        read: false,
      },
    ];

    render(
      <MemoryRouter>
        <Header {...defaultProps} notifications={notifications} unreadCount={2} />
      </MemoryRouter>
    );

    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('applies correct navigation link hrefs', () => {
    render(
      <MemoryRouter>
        <Header {...defaultProps} />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: 'Theme Analysis' })).toHaveAttribute('href', '/themes');
  });
});
