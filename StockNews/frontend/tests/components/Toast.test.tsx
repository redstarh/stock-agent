import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Toast from '../../src/components/common/Toast';

describe('Toast', () => {
  it('displays breaking news message', () => {
    render(<Toast message="속보: 삼성전자 실적 발표" onClose={() => {}} />);
    expect(screen.getByText('속보: 삼성전자 실적 발표')).toBeInTheDocument();
  });

  it('auto-dismisses after 5 seconds', () => {
    vi.useFakeTimers();
    const onClose = vi.fn();
    render(<Toast message="테스트" onClose={onClose} duration={5000} />);

    expect(onClose).not.toHaveBeenCalled();
    vi.advanceTimersByTime(5000);
    expect(onClose).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('closes on close button click', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Toast message="테스트" onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: '닫기' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
