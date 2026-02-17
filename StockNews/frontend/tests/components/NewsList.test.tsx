import { render, screen } from '@testing-library/react';
import NewsList from '../../src/components/news/NewsList';
import type { NewsItem } from '../../src/types/news';

const items: NewsItem[] = [
  {
    id: 1,
    title: '삼성전자 실적 발표',
    stock_code: '005930',
    stock_name: '삼성전자',
    sentiment: 'positive',
    news_score: 85.5,
    source: 'naver',
    source_url: null,
    market: 'KR',
    theme: null,
    published_at: '2024-01-15T09:00:00+09:00',
  },
  {
    id: 2,
    title: 'SK하이닉스 HBM 수주',
    stock_code: '000660',
    stock_name: 'SK하이닉스',
    sentiment: 'neutral',
    news_score: 72.3,
    source: 'naver',
    source_url: null,
    market: 'KR',
    theme: null,
    published_at: '2024-01-15T08:30:00+09:00',
  },
];

describe('NewsList', () => {
  it('renders all news items', () => {
    render(<NewsList items={items} />);
    expect(screen.getByText('삼성전자 실적 발표')).toBeInTheDocument();
    expect(screen.getByText('SK하이닉스 HBM 수주')).toBeInTheDocument();
  });

  it('shows empty message when no items', () => {
    render(<NewsList items={[]} />);
    expect(screen.getByText('뉴스가 없습니다')).toBeInTheDocument();
  });
});
