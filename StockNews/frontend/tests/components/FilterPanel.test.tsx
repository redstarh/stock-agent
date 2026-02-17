import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import FilterPanel, { DEFAULT_FILTERS } from '../../src/components/common/FilterPanel';

describe('FilterPanel', () => {
  const themes = ['반도체', '2차전지', 'AI/로봇'];

  it('renders filter controls', () => {
    render(<FilterPanel filters={DEFAULT_FILTERS} themes={themes} onChange={() => {}} />);
    expect(screen.getByText('기간')).toBeInTheDocument();
    expect(screen.getByText('감성')).toBeInTheDocument();
    expect(screen.getByText('테마')).toBeInTheDocument();
  });

  it('shows theme options', () => {
    render(<FilterPanel filters={DEFAULT_FILTERS} themes={themes} onChange={() => {}} />);
    const themeSelect = screen.getAllByRole('combobox')[1]; // second select
    expect(themeSelect).toBeInTheDocument();
  });

  it('calls onChange when sentiment changes', () => {
    const onChange = vi.fn();
    render(<FilterPanel filters={DEFAULT_FILTERS} themes={themes} onChange={onChange} />);
    const sentimentSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(sentimentSelect, { target: { value: 'positive' } });
    expect(onChange).toHaveBeenCalledWith({ ...DEFAULT_FILTERS, sentiment: 'positive' });
  });

  it('calls reset', () => {
    const onChange = vi.fn();
    const modified = { ...DEFAULT_FILTERS, sentiment: 'positive' as const };
    render(<FilterPanel filters={modified} themes={themes} onChange={onChange} />);
    fireEvent.click(screen.getByText('초기화'));
    expect(onChange).toHaveBeenCalledWith(DEFAULT_FILTERS);
  });
});
