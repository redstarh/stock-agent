import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('App renders without crashing', () => {
  render(<App />);
  expect(screen.getByRole('main')).toBeInTheDocument();
});

test('App displays StockNews title', () => {
  render(<App />);
  expect(screen.getByText('StockNews')).toBeInTheDocument();
});
