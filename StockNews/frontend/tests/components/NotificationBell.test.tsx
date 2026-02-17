import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NotificationBell from '../../src/components/common/NotificationBell';
import type { WebSocketMessage } from '../../src/types/api';

const notifications: WebSocketMessage[] = [
  { type: 'breaking_news', data: { title: '속보: 삼성전자' } },
  { type: 'breaking_news', data: { title: '속보: SK하이닉스' } },
  { type: 'score_update', data: { stock_code: '005930', score: 90 } },
];

describe('NotificationBell', () => {
  it('shows unread count badge', () => {
    render(<NotificationBell notifications={notifications} />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows dropdown on click', async () => {
    const user = userEvent.setup();
    render(<NotificationBell notifications={notifications} />);

    await user.click(screen.getByRole('button', { name: '알림' }));
    expect(screen.getByText('속보: 삼성전자')).toBeInTheDocument();
    expect(screen.getByText('속보: SK하이닉스')).toBeInTheDocument();
  });

  it('shows notification history list', async () => {
    const user = userEvent.setup();
    render(<NotificationBell notifications={notifications} />);

    await user.click(screen.getByRole('button', { name: '알림' }));
    // All 3 notifications in the dropdown
    const items = screen.getAllByRole('listitem');
    expect(items).toHaveLength(3);
  });

  it('hides badge when no notifications', () => {
    render(<NotificationBell notifications={[]} />);
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });
});
