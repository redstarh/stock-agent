import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Loading from '../../src/components/common/Loading';

describe('Loading', () => {
  test('스피너가 렌더링됨', () => {
    render(<Loading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('기본 메시지 표시', () => {
    render(<Loading />);
    expect(screen.getByText('로딩 중...')).toBeInTheDocument();
  });

  test('커스텀 메시지 표시', () => {
    render(<Loading message="데이터 불러오는 중..." />);
    expect(screen.getByText('데이터 불러오는 중...')).toBeInTheDocument();
  });
});
