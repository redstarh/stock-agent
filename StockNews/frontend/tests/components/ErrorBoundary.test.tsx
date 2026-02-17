import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../../src/components/common/ErrorBoundary';

function ThrowingChild(): JSX.Element {
  throw new Error('test error');
}

describe('ErrorBoundary', () => {
  test('자식 에러 발생 시 fallback UI 표시', () => {
    // console.error 억제
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>,
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();

    vi.restoreAllMocks();
  });

  test('정상 시 자식 컴포넌트 렌더링', () => {
    render(
      <ErrorBoundary>
        <p>정상 컴포넌트</p>
      </ErrorBoundary>,
    );

    expect(screen.getByText('정상 컴포넌트')).toBeInTheDocument();
  });
});
