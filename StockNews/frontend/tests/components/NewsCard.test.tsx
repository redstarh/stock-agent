import { render, screen } from '@testing-library/react';
import NewsCard from '../../src/components/news/NewsCard';
import type { NewsItem } from '../../src/types/news';

const item: NewsItem = {
  id: 1,
  title: '삼성전자 실적 발표',
  stock_code: '005930',
  stock_name: '삼성전자',
  sentiment: 'positive',
  news_score: 85.5,
  source: 'naver',
  source_url: 'https://news.naver.com/1',
  market: 'KR',
  theme: 'AI',
  published_at: '2024-01-15T09:00:00+09:00',
};

describe('NewsCard', () => {
  it('renders title', () => {
    render(<NewsCard item={item} />);
    expect(screen.getByText('삼성전자 실적 발표')).toBeInTheDocument();
  });

  it('renders sentiment label in Korean', () => {
    render(<NewsCard item={item} />);
    expect(screen.getByText('긍정')).toBeInTheDocument();
  });

  it('renders stock name', () => {
    render(<NewsCard item={item} />);
    expect(screen.getByText('삼성전자')).toBeInTheDocument();
  });

  it('renders score', () => {
    render(<NewsCard item={item} />);
    expect(screen.getByText('Score: 85.5')).toBeInTheDocument();
  });

  it('renders source', () => {
    render(<NewsCard item={item} />);
    expect(screen.getByText('naver')).toBeInTheDocument();
  });

  it('falls back to stock_code when stock_name is null', () => {
    const noNameItem: NewsItem = { ...item, stock_name: null };
    render(<NewsCard item={noNameItem} />);
    expect(screen.getByText('005930')).toBeInTheDocument();
  });
});
