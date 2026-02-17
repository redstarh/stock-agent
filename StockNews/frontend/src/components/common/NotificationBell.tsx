import { useState } from 'react';
import type { WebSocketMessage } from '../../types/api';

interface NotificationBellProps {
  notifications: WebSocketMessage[];
}

function formatNotification(msg: WebSocketMessage): string {
  if (msg.data && typeof msg.data.title === 'string') {
    return msg.data.title;
  }
  if (msg.data && msg.data.stock_code) {
    return `${msg.type}: ${msg.data.stock_code}`;
  }
  return msg.type;
}

export default function NotificationBell({ notifications }: NotificationBellProps) {
  const [open, setOpen] = useState(false);

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
        {notifications.length > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {notifications.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-40 mt-2 w-72 rounded-lg border bg-white shadow-lg">
          <div className="border-b px-4 py-2 text-sm font-semibold text-gray-700">
            알림 ({notifications.length})
          </div>
          {notifications.length === 0 ? (
            <p className="px-4 py-3 text-sm text-gray-400">알림이 없습니다</p>
          ) : (
            <ul className="max-h-60 overflow-y-auto">
              {notifications.map((msg, idx) => (
                <li
                  key={idx}
                  className="border-b px-4 py-2 text-sm text-gray-700 last:border-b-0 hover:bg-gray-50"
                >
                  {formatNotification(msg)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
