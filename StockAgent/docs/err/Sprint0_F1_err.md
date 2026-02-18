# Sprint 0 - F-1 에러 기록

## [에러 1] jest.config.ts setupFilesAfterSetup 오타
- **단계**: GREEN (Jest 설정)
- **에러**: TypeScript 타입 에러 — `setupFilesAfterSetup` does not exist
- **원인**: 올바른 속성명은 `setupFilesAfterEnv`
- **해결**: `setupFilesAfterEnv`로 수정

## [에러 2] next/jest 모듈 import 오류
- **단계**: GREEN (테스트 실행)
- **에러**: `Cannot find module 'next/jest'` — Jest 30 + Next.js 16 호환 이슈
- **원인**: ESM 모듈 해석에서 `next/jest`를 찾지 못함, 명시적 확장자 필요
- **해결**: `import nextJest from "next/jest.js"`로 확장자 명시

## 최종 결과
- 테스트 3/3 통과
- Navigation 컴포넌트, 라우트 페이지 모두 정상
