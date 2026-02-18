# Sprint 1 - B-11 에러 기록

## [에러 1] import 누락 + respx assert_all_called 충돌
- **단계**: GREEN (테스트 실행)
- **에러**: `NameError: name 'NewsClient' is not defined` + `AssertionError: RESPX: some routes were not called!`
- **원인**:
  1. `test_news_service_unavailable`에서 `NewsClient` import 누락
  2. fixture의 `params=005930` 라우트가 503 오버라이드 테스트에서 호출되지 않아 respx가 assert_all_called 에러 발생
- **해결**:
  1. 모듈 레벨에서 `from src.core.news_client import NewsClient` 추가
  2. fixture에 `assert_all_called=False` 설정
  3. 503 테스트는 별도 `respx.mock` context manager 사용

## 최종 결과
- 테스트 4/4 통과
- Backend 전체 24/24 통과
