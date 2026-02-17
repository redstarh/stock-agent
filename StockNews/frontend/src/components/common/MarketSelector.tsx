import { MARKETS, type Market } from '../../utils/constants';

interface MarketSelectorProps {
  selected: Market;
  onChange: (market: Market) => void;
}

export default function MarketSelector({ selected, onChange }: MarketSelectorProps) {
  return (
    <div role="tablist" className="flex gap-1 rounded-lg bg-gray-100 p-1">
      {MARKETS.map((market) => (
        <button
          key={market}
          role="tab"
          aria-selected={selected === market}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition ${
            selected === market
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => onChange(market)}
        >
          {market}
        </button>
      ))}
    </div>
  );
}
