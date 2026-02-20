import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import StockResultsTable from '../../../src/components/verification/StockResultsTable';
import type { DailyPredictionResult } from '../../../src/types/verification';

const mockResults: DailyPredictionResult[] = [
  {
    stock_code: '005930',
    stock_name: '삼성전자',
    predicted_direction: 'up',
    predicted_score: 85.5,
    confidence: 0.85,
    actual_direction: 'up',
    actual_change_pct: 2.5,
    is_correct: true,
    news_count: 12,
    error_message: null,
  },
  {
    stock_code: '000660',
    stock_name: 'SK하이닉스',
    predicted_direction: 'down',
    predicted_score: 72.3,
    confidence: 0.75,
    actual_direction: 'up',
    actual_change_pct: 1.2,
    is_correct: false,
    news_count: 8,
    error_message: null,
  },
  {
    stock_code: '035720',
    stock_name: '카카오',
    predicted_direction: 'neutral',
    predicted_score: 55.0,
    confidence: 0.60,
    actual_direction: null,
    actual_change_pct: null,
    is_correct: null,
    news_count: 5,
    error_message: null,
  },
];

describe('StockResultsTable', () => {
  it('renders empty state when no results', () => {
    render(<StockResultsTable results={[]} />);
    expect(screen.getByText('검증 결과가 없습니다')).toBeInTheDocument();
  });

  it('renders table with all results', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByText('삼성전자')).toBeInTheDocument();
    expect(screen.getByText('SK하이닉스')).toBeInTheDocument();
    expect(screen.getByText('카카오')).toBeInTheDocument();
  });

  it('displays stock codes for each result', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByText('005930')).toBeInTheDocument();
    expect(screen.getByText('000660')).toBeInTheDocument();
    expect(screen.getByText('035720')).toBeInTheDocument();
  });

  it('shows predicted direction arrows', () => {
    render(<StockResultsTable results={mockResults} />);
    const upArrows = screen.getAllByText('▲');
    const downArrows = screen.getAllByText('▼');
    const neutralMarks = screen.getAllByText('—');
    expect(upArrows.length).toBeGreaterThan(0);
    expect(downArrows.length).toBeGreaterThan(0);
    expect(neutralMarks.length).toBeGreaterThan(0);
  });

  it('displays actual change percentage with correct formatting', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByText('+2.50%')).toBeInTheDocument();
    expect(screen.getByText('+1.20%')).toBeInTheDocument();
  });

  it('displays confidence as percentage', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByText('85.0%')).toBeInTheDocument();
    expect(screen.getByText('75.0%')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
  });

  it('shows correct/incorrect badges', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByText('✓')).toBeInTheDocument();
    expect(screen.getByText('✗')).toBeInTheDocument();
  });

  it('handles null actual values gracefully', () => {
    render(<StockResultsTable results={mockResults} />);
    const nullMarkers = screen.getAllByText('-');
    expect(nullMarkers.length).toBeGreaterThan(0);
  });

  it('sorts by stock_code when column header clicked', async () => {
    const user = userEvent.setup();
    render(<StockResultsTable results={mockResults} />);

    const stockCodeButton = screen.getByRole('button', { name: /종목/ });
    await user.click(stockCodeButton);

    // Check for sort indicator
    expect(screen.getByText(/종목.*↓/)).toBeInTheDocument();
  });

  it('sorts by actual_change_pct when column header clicked', async () => {
    const user = userEvent.setup();
    render(<StockResultsTable results={mockResults} />);

    const changeButton = screen.getByRole('button', { name: /변동률/ });
    await user.click(changeButton);

    expect(screen.getByText(/변동률.*↓/)).toBeInTheDocument();
  });

  it('sorts by confidence when column header clicked', async () => {
    const user = userEvent.setup();
    render(<StockResultsTable results={mockResults} />);

    const confidenceButton = screen.getByRole('button', { name: /신뢰도/ });
    await user.click(confidenceButton);

    expect(screen.getByText(/신뢰도.*↓/)).toBeInTheDocument();
  });

  it('toggles sort direction on repeated clicks', async () => {
    const user = userEvent.setup();
    render(<StockResultsTable results={mockResults} />);

    const stockCodeButton = screen.getByRole('button', { name: /종목/ });
    await user.click(stockCodeButton);
    expect(screen.getByText(/종목.*↓/)).toBeInTheDocument();

    await user.click(stockCodeButton);
    expect(screen.getByText(/종목.*↑/)).toBeInTheDocument();
  });

  it('renders table with proper structure', () => {
    render(<StockResultsTable results={mockResults} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays stock code when name is missing', () => {
    const resultsWithoutName = [
      { ...mockResults[0], stock_name: null },
    ];
    render(<StockResultsTable results={resultsWithoutName} />);
    const codeElements = screen.getAllByText('005930');
    expect(codeElements.length).toBeGreaterThan(0);
  });
});
