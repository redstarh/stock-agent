import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChartDrilldown from '../../src/components/charts/ChartDrilldown';

const mockNews = [
  {
    id: 1,
    title: '테스트 뉴스 1',
    stock_code: '005930',
    stock_name: '삼성전자',
    sentiment: 'positive' as const,
    news_score: 85,
    source: 'Naver',
    source_url: null,
    market: 'KR',
    theme: '반도체',
    published_at: '2026-02-18T10:00:00',
  },
];

describe('ChartDrilldown', () => {
  it('renders nothing when date is null', () => {
    const { container } = render(<ChartDrilldown date={null} news={[]} onClose={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it('shows date header and news list', () => {
    render(<ChartDrilldown date="2026-02-18" news={mockNews} onClose={() => {}} />);
    expect(screen.getByText('2026-02-18 뉴스')).toBeInTheDocument();
    expect(screen.getByText('테스트 뉴스 1')).toBeInTheDocument();
  });

  it('shows empty message when no news', () => {
    render(<ChartDrilldown date="2026-02-18" news={[]} onClose={() => {}} />);
    expect(screen.getByText('해당 날짜의 뉴스가 없습니다')).toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(<ChartDrilldown date="2026-02-18" news={mockNews} onClose={onClose} />);
    fireEvent.click(screen.getByText('닫기'));
    expect(onClose).toHaveBeenCalled();
  });
});
