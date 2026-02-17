import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div role="alert" className="p-6 text-center">
          <p className="text-lg font-semibold text-red-600">오류가 발생했습니다</p>
          <p className="mt-2 text-sm text-gray-500">잠시 후 다시 시도해 주세요</p>
        </div>
      );
    }
    return this.props.children;
  }
}
