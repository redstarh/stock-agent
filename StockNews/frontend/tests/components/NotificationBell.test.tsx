import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import NotificationBell from '../../src/components/common/NotificationBell';
import type { Notification } from '../../src/hooks/useWebSocket';

const notifications: Notification[] = [
  {
    id: '1',
    message: { type: 'breaking_news', data: { title: '속보: 삼성전자', stock_code: '005930' } },
    timestamp: Date.now(),
    read: false,
  },
  {
    id: '2',
    message: { type: 'breaking_news', data: { title: '속보: SK하이닉스', stock_code: '000660' } },
    timestamp: Date.now(),
    read: false,
  },
  {
    id: '3',
    message: { type: 'score_update', data: { stock_code: '005930', score: 90 } },
    timestamp: Date.now(),
    read: true,
  },
];

describe('NotificationBell', () => {
  it('shows unread count badge', () => {
    render(
      <NotificationBell
        notifications={notifications}
        unreadCount={2}
        onMarkAsRead={vi.fn()}
        onMarkAllAsRead={vi.fn()}
        onClear={vi.fn()}
      />
    );
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows dropdown on click', async () => {
    const user = userEvent.setup();
    render(
      <NotificationBell
        notifications={notifications}
        unreadCount={2}
        onMarkAsRead={vi.fn()}
        onMarkAllAsRead={vi.fn()}
        onClear={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: '알림' }));
    expect(screen.getByText('속보: 삼성전자')).toBeInTheDocument();
    expect(screen.getByText('속보: SK하이닉스')).toBeInTheDocument();
  });

  it('shows notification history list', async () => {
    const user = userEvent.setup();
    render(
      <NotificationBell
        notifications={notifications}
        unreadCount={2}
        onMarkAsRead={vi.fn()}
        onMarkAllAsRead={vi.fn()}
        onClear={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: '알림' }));
    // All 3 notifications in the dropdown
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
  });

  it('hides badge when no notifications', () => {
    render(
      <NotificationBell
        notifications={[]}
        unreadCount={0}
        onMarkAsRead={vi.fn()}
        onMarkAllAsRead={vi.fn()}
        onClear={vi.fn()}
      />
    );
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });
});
