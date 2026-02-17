# Task [3] Backend: News Collector — 오류 기록

## 오류 없음

Task [3]은 TDD 사이클 (RED → GREEN → VERIFY) 과정에서 오류 없이 완료됨.

## 참고 사항

- Naver 크롤러: `HTMLParser` 기반 파싱 (BeautifulSoup 의존성 불필요)
- DART 수집기: `respx`로 HTTP mock, `status != "000"` 시 빈 리스트 반환
- RSS 파서: `xml.etree.ElementTree` 사용, malformed XML에 대한 graceful 처리
- 스케줄러: APScheduler `BackgroundScheduler` + 5분 interval
- 중복제거: URL 기반 1순위, 제목 기반 2순위 판별

## 최종 결과

- **테스트**: 67 passed (전체)
- **Task [3] 테스트**: 15 passed (dedup 5 + collectors 10)
- **커버리지**: 92.88% (전체), collectors 83-96%, dedup 96%
