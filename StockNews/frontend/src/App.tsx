import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardPage from './pages/DashboardPage';
import StockDetailPage from './pages/StockDetailPage';
import ThemeAnalysisPage from './pages/ThemeAnalysisPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <main className="min-h-screen bg-gray-50">
          <header className="border-b bg-white px-6 py-3">
            <h1 className="text-xl font-bold text-blue-600">StockNews</h1>
          </header>
          <div className="mx-auto max-w-7xl px-4 py-6">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/stocks/:code" element={<StockDetailPage />} />
              <Route path="/themes" element={<ThemeAnalysisPage />} />
            </Routes>
          </div>
        </main>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
