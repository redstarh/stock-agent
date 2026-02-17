import { describe, test, expect } from 'vitest';
import { formatDateTime, formatScore, formatSentiment } from '../../src/utils/format';
import { MARKETS, SENTIMENT_COLORS, REFRESH_INTERVAL_MS } from '../../src/utils/constants';

describe('formatDateTime', () => {
  test('ISO 문자열 → 한국어 포맷', () => {
    const result = formatDateTime('2024-01-15T09:00:00+09:00');
    expect(result).toContain('2024');
    expect(result).not.toBe('-');
  });

  test('null → "-"', () => {
    expect(formatDateTime(null)).toBe('-');
  });

  test('잘못된 날짜 → "-"', () => {
    expect(formatDateTime('not-a-date')).toBe('-');
  });
});

describe('formatScore', () => {
  test('소수점 1자리 반환', () => {
    expect(formatScore(85.567)).toBe('85.6');
    expect(formatScore(0)).toBe('0.0');
  });
});

describe('formatSentiment', () => {
  test('한글 라벨 반환', () => {
    expect(formatSentiment('positive')).toBe('긍정');
    expect(formatSentiment('neutral')).toBe('중립');
    expect(formatSentiment('negative')).toBe('부정');
  });

  test('미등록 값 → 원본 반환', () => {
    expect(formatSentiment('unknown')).toBe('unknown');
  });
});

describe('constants', () => {
  test('MARKETS에 KR, US 포함', () => {
    expect(MARKETS).toContain('KR');
    expect(MARKETS).toContain('US');
  });

  test('SENTIMENT_COLORS 정의됨', () => {
    expect(SENTIMENT_COLORS.positive).toBeDefined();
    expect(SENTIMENT_COLORS.negative).toBeDefined();
  });

  test('REFRESH_INTERVAL_MS가 30초', () => {
    expect(REFRESH_INTERVAL_MS).toBe(30_000);
  });
});
