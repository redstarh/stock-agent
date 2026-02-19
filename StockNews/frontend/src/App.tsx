import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import NewsPage from './pages/NewsPage';
import StockDetailPage from './pages/StockDetailPage';
import ThemeAnalysisPage from './pages/ThemeAnalysisPage';
import Toast from './components/common/Toast';
import { useWebSocket } from './hooks/useWebSocket';
import type { BreakingNewsData } from './types/api';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
    },
  },
});

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws/news';

export default function App() {
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleBreakingNews = (data: BreakingNewsData) => {
    const message = `🚨 ${data.stock_name || data.stock_code}: ${data.title}`;
    setToastMessage(message);
  };

  const {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    clearNotifications,
  } = useWebSocket(WS_URL, handleBreakingNews);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout
          notifications={notifications}
          unreadCount={unreadCount}
          onMarkAsRead={markAsRead}
          onMarkAllAsRead={markAllAsRead}
          onClearNotifications={clearNotifications}
        >
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/news" element={<NewsPage />} />
            <Route path="/stocks/:code" element={<StockDetailPage />} />
            <Route path="/themes" element={<ThemeAnalysisPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>

      {toastMessage && (
        <Toast message={toastMessage} onClose={() => setToastMessage(null)} />
      )}
    </QueryClientProvider>
  );
}
