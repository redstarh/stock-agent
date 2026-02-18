import { Link } from 'react-router-dom';
import NotificationBell from '../common/NotificationBell';
import type { Notification } from '../../hooks/useWebSocket';

interface HeaderProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onClearNotifications: () => void;
}

export default function Header({
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onClearNotifications,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b bg-white px-6 py-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-blue-600 hover:text-blue-700">
            StockNews
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition"
            >
              Dashboard
            </Link>
            <Link
              to="/themes"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition"
            >
              Theme Analysis
            </Link>
          </nav>
        </div>
        <NotificationBell
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkAsRead={onMarkAsRead}
          onMarkAllAsRead={onMarkAllAsRead}
          onClear={onClearNotifications}
        />
      </div>
    </header>
  );
}
