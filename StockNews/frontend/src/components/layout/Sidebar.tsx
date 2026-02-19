import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import MarketSelector from '../common/MarketSelector';
import type { Market } from '../../utils/constants';

interface SidebarProps {
  market: Market;
  onMarketChange: (market: Market) => void;
}

export default function Sidebar({ market, onMarketChange }: SidebarProps) {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/news', label: 'Latest News', icon: '📰' },
    { path: '/themes', label: 'Theme Analysis', icon: '🎯' },
  ];

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        className="fixed left-4 top-4 z-50 rounded-md bg-white p-2 shadow-md lg:hidden"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle menu"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        role="complementary"
        className={`fixed left-0 top-0 z-40 h-screen w-64 transform border-r bg-white transition-transform lg:sticky lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col p-4">
          <div className="mb-8 mt-16 lg:mt-4">
            <h2 className="text-lg font-bold text-gray-800">Navigation</h2>
          </div>

          <nav className="flex-1 space-y-2">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
                    isActive
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="border-t pt-4">
            <p className="mb-2 text-xs font-semibold text-gray-500">Market</p>
            <MarketSelector selected={market} onChange={onMarketChange} />
          </div>
        </div>
      </aside>
    </>
  );
}
