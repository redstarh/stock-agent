import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import NewsCard from '../../src/components/news/NewsCard';
import type { NewsItem } from '../../src/types/news';

describe('NewsCard', () => {
  const baseItem: NewsItem = {
    id: 1,
    title: '삼성전자 4분기 실적 발표',
    stock_code: '005930',
    stock_name: '삼성전자',
    sentiment: 'positive',
    news_score: 85.0,
    source: 'naver',
    source_url: 'https://example.com',
    market: 'KR',
    theme: 'AI',
    published_at: '2024-01-15T09:00:00Z',
  };

  it('renders title and basic info', () => {
    render(<NewsCard item={baseItem} />);
    expect(screen.getByText('삼성전자 4분기 실적 발표')).toBeInTheDocument();
    expect(screen.getByText('삼성전자')).toBeInTheDocument();
  });

  it('renders summary when present', () => {
    const itemWithSummary: NewsItem = {
      ...baseItem,
      summary: '삼성전자가 4분기 사상 최대 실적을 기록했다.',
    };
    render(<NewsCard item={itemWithSummary} />);
    expect(screen.getByText('삼성전자가 4분기 사상 최대 실적을 기록했다.')).toBeInTheDocument();
  });

  it('does not render summary paragraph when summary is null', () => {
    const itemNoSummary: NewsItem = {
      ...baseItem,
      summary: null,
    };
    const { container } = render(<NewsCard item={itemNoSummary} />);
    const summaryParagraph = container.querySelector('p.text-gray-600');
    expect(summaryParagraph).not.toBeInTheDocument();
  });

  it('does not render summary paragraph when summary is undefined', () => {
    const itemNoSummary: NewsItem = {
      ...baseItem,
      summary: undefined,
    };
    const { container } = render(<NewsCard item={itemNoSummary} />);
    const summaryParagraph = container.querySelector('p.text-gray-600');
    expect(summaryParagraph).not.toBeInTheDocument();
  });

  it('does not render summary paragraph when summary is empty string', () => {
    const itemEmptySummary: NewsItem = {
      ...baseItem,
      summary: '',
    };
    const { container } = render(<NewsCard item={itemEmptySummary} />);
    const summaryParagraph = container.querySelector('p.text-gray-600');
    expect(summaryParagraph).not.toBeInTheDocument();
  });

  it('applies line-clamp-2 class to summary', () => {
    const itemWithSummary: NewsItem = {
      ...baseItem,
      summary: '삼성전자가 4분기 사상 최대 실적을 기록했다.',
    };
    const { container } = render(<NewsCard item={itemWithSummary} />);
    const summaryParagraph = container.querySelector('p.line-clamp-2');
    expect(summaryParagraph).toBeInTheDocument();
  });
});
