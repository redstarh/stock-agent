import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TopStockCards from '../../src/components/news/TopStockCards';
import type { NewsTopItem } from '../../src/types/news';

const items: NewsTopItem[] = [
  {
    stock_code: '005930',
    stock_name: '삼성전자',
    news_score: 85.5,
    sentiment: 'positive',
    news_count: 12,
    market: 'KR',
    prediction_score: 75.2,
    direction: 'up',
  },
  {
    stock_code: '000660',
    stock_name: 'SK하이닉스',
    news_score: 72.3,
    sentiment: 'neutral',
    news_count: 8,
    market: 'KR',
    prediction_score: 55.8,
    direction: 'neutral',
  },
];

describe('TopStockCards', () => {
  it('renders stock names', () => {
    render(<TopStockCards items={items} />);
    expect(screen.getByText('삼성전자')).toBeInTheDocument();
    expect(screen.getByText('SK하이닉스')).toBeInTheDocument();
  });

  it('renders prediction scores formatted', () => {
    render(<TopStockCards items={items} />);
    expect(screen.getByText(/75\.2/)).toBeInTheDocument();
    expect(screen.getByText(/55\.8/)).toBeInTheDocument();
  });

  it('renders sentiment labels in Korean', () => {
    render(<TopStockCards items={items} />);
    expect(screen.getByText('긍정')).toBeInTheDocument();
    expect(screen.getByText('중립')).toBeInTheDocument();
  });

  it('renders direction labels and news count', () => {
    render(<TopStockCards items={items} />);
    expect(screen.getByText(/상승 예측.*뉴스 12건/)).toBeInTheDocument();
    expect(screen.getByText(/중립.*뉴스 8건/)).toBeInTheDocument();
  });

  it('calls onStockClick with stock code when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<TopStockCards items={items} onStockClick={handleClick} />);

    await user.click(screen.getByText('삼성전자'));
    expect(handleClick).toHaveBeenCalledWith('005930');
  });

  it('falls back to stock_code when stock_name is null', () => {
    const noNameItems: NewsTopItem[] = [
      { ...items[0], stock_name: null },
    ];
    render(<TopStockCards items={noNameItems} />);
    expect(screen.getByText('005930')).toBeInTheDocument();
  });
});
