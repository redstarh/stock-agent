import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Market } from '../utils/constants';

interface MarketContextValue {
  market: Market;
  setMarket: (market: Market) => void;
}

const MarketContext = createContext<MarketContextValue | null>(null);

export function MarketProvider({ children }: { children: ReactNode }) {
  const [market, setMarket] = useState<Market>('KR');
  return (
    <MarketContext.Provider value={{ market, setMarket }}>
      {children}
    </MarketContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useMarket(): MarketContextValue {
  const ctx = useContext(MarketContext);
  if (!ctx) throw new Error('useMarket must be used within MarketProvider');
  return ctx;
}
