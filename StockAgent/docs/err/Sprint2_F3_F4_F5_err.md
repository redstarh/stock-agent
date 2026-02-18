# Sprint 2 - F-3/F-4/F-5 에러 기록

## [에러 1] jsdom + MSW: Response is not defined
- **단계**: GREEN (테스트 실행)
- **에러**: `ReferenceError: Response is not defined` (F-4, F-5)
- **원인**: jsdom 환경에 Fetch API (Response, Request, Headers) 미포함. MSW v2가 모듈 로드 시 Response 참조
- **F-3 영향 없음**: AuthSettings는 MSW 미사용

## [에러 2] undici polyfill 시 TextDecoder 누락
- **단계**: GREEN (polyfill 시도)
- **에러**: `ReferenceError: TextDecoder is not defined`
- **원인**: undici가 내부적으로 TextDecoder 사용하지만 jsdom 환경에서 미정의
- **시도**: `tests/setup.ts`에서 `import { Response, Request, Headers, fetch } from "undici"` → 실패

## 해결 방향 (미완료)
1. TextEncoder/TextDecoder polyfill 추가 후 undici import
2. jest.config.ts의 `setupFiles`로 polyfill 이동
3. `jest-fixed-jsdom` 패키지 사용

## 현재 상태
- F-3 AuthSettings: 3/3 통과
- F-4 Dashboard: 에러 (미해결)
- F-5 PositionList: 에러 (미해결)
