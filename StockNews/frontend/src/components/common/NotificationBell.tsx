import { useState } from 'react';
import type { Notification } from '../../hooks/useWebSocket';

interface NotificationBellProps {
  notifications: Notification[];
  unreadCount: number;
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
  onClear: () => void;
}

function formatNotification(notification: Notification): string {
  const { message } = notification;
  if (message.data && typeof message.data.title === 'string') {
    return message.data.title as string;
  }
  if (message.data && message.data.stock_code) {
    return `${message.type}: ${message.data.stock_code}`;
  }
  return message.type;
}

function formatTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);

  if (minutes < 1) return '방금';
  if (minutes < 60) return `${minutes}분 전`;
  if (hours < 24) return `${hours}시간 전`;
  return new Date(timestamp).toLocaleDateString('ko-KR');
}

export default function NotificationBell({
  notifications,
  unreadCount,
  onMarkAsRead,
  onMarkAllAsRead,
  onClear,
}: NotificationBellProps) {
  const [open, setOpen] = useState(false);

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
  };

  return (
    <div className="relative">
      <button
        aria-label="알림"
        className="relative rounded-md p-2 text-gray-600 hover:bg-gray-100"
        onClick={() => setOpen((prev) => !prev)}
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-40 mt-2 w-80 rounded-lg border bg-white shadow-lg">
          <div className="flex items-center justify-between border-b px-4 py-2">
            <span className="text-sm font-semibold text-gray-700">
              알림 {unreadCount > 0 && `(${unreadCount})`}
            </span>
            <div className="flex gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={onMarkAllAsRead}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  모두 읽음
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={() => {
                    onClear();
                    setOpen(false);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  전체 삭제
                </button>
              )}
            </div>
          </div>
          {notifications.length === 0 ? (
            <p className="px-4 py-3 text-sm text-gray-400">알림이 없습니다</p>
          ) : (
            <ul className="max-h-60 overflow-y-auto">
              {notifications.map((notif) => (
                <li
                  key={notif.id}
                  onClick={() => handleNotificationClick(notif)}
                  className={`cursor-pointer border-b px-4 py-2 last:border-b-0 hover:bg-gray-50 ${
                    !notif.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className={`text-sm ${!notif.read ? 'font-semibold text-gray-900' : 'text-gray-700'}`}>
                        {formatNotification(notif)}
                      </p>
                      {notif.message.data?.stock_code && (
                        <p className="mt-1 text-xs text-gray-500">
                          {notif.message.data.stock_code} {notif.message.data.stock_name}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className="text-xs text-gray-400">{formatTime(notif.timestamp)}</span>
                      {!notif.read && (
                        <span className="h-2 w-2 rounded-full bg-blue-500"></span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
