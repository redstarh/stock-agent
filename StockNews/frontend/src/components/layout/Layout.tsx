import { ReactNode } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import { useMarket } from '../../contexts/MarketContext';
import type { Notification } from '../../hooks/useWebSocket';

interface LayoutProps {
  children: ReactNode;
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onClearNotifications: () => void;
}

export default function Layout({
  children,
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onClearNotifications,
}: LayoutProps) {
  const { market, setMarket } = useMarket();

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar market={market} onMarketChange={setMarket} />
      <div className="flex flex-1 flex-col">
        <Header
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkAsRead={onMarkAsRead}
          onMarkAllAsRead={onMarkAllAsRead}
          onClearNotifications={onClearNotifications}
        />
        <main className="flex-1 p-6">
          <div className="mx-auto max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
