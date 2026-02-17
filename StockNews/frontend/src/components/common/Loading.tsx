interface LoadingProps {
  message?: string;
}

export default function Loading({ message = '로딩 중...' }: LoadingProps) {
  return (
    <div role="status" aria-label="loading" className="flex flex-col items-center justify-center p-8">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
      <p className="mt-3 text-sm text-gray-500">{message}</p>
    </div>
  );
}
