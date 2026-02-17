/** 날짜 포맷팅 유틸리티 */

/** ISO 문자열 → 'YYYY-MM-DD HH:mm' */
export function formatDateTime(iso: string | null): string {
  if (!iso) return '-';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** 숫자 → 소수점 1자리 */
export function formatScore(score: number): string {
  return score.toFixed(1);
}

/** 감성 → 한글 라벨 */
export function formatSentiment(sentiment: string): string {
  const labels: Record<string, string> = {
    positive: '긍정',
    neutral: '중립',
    negative: '부정',
  };
  return labels[sentiment] ?? sentiment;
}
