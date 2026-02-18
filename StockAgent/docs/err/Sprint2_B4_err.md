# Sprint 2 - B-4 에러 기록

## [에러 1] respx assert_all_called 충돌
- **단계**: GREEN (테스트 실행)
- **에러**: `AssertionError: RESPX: some routes were not called!`
- **원인**: `mock_kiwoom` fixture가 price + orderbook 두 라우트를 등록하지만, 각 테스트는 하나만 호출하여 teardown 시 respx가 미호출 라우트 에러 발생
- **해결**: fixture에 `assert_all_called=False` 설정

## 최종 결과
- 테스트 4/4 통과
- Backend 전체 28/28 통과
