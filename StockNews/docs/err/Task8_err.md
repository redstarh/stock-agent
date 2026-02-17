# Task [8] Frontend: 프로젝트 설정 + 레이아웃 — 오류 기록

## ERR-8-1: erasableSyntaxOnly TypeScript 에러

- **증상**: `This syntax is not allowed when 'erasableSyntaxOnly' is enabled. [1294]` — `client.ts` line 8
- **원인**: `tsconfig.app.json`에 `erasableSyntaxOnly: true` 설정 시 parameter property (`public status: number`) 사용 불가
- **수정**: `ApiError` 클래스에서 `public` parameter property 제거, 별도 필드 선언으로 변경
- **영향 파일**: `src/api/client.ts`

## ERR-8-2: @vitest/coverage-v8 미설치

- **증상**: `Cannot find dependency '@vitest/coverage-v8'`
- **수정**: `npm install -D @vitest/coverage-v8`
- **영향**: devDependencies 추가

## ERR-8-3: 커버리지 임계값 미달 (types + utils 0%)

- **증상**: `Coverage for statements (68%) does not meet global threshold (70%)`
- **원인**: `src/types/*.ts` (인터페이스만 정의, 런타임 코드 없음)가 0%로 집계, `src/utils/` 테스트 미작성
- **수정**:
  1. `vite.config.ts` coverage exclude에 `src/types/**` 추가
  2. `tests/utils/format.test.ts` 작성 (format + constants 테스트)
- **영향 파일**: `vite.config.ts`, `tests/utils/format.test.ts` (신규)

## 최종 결과

- **테스트**: 24 passed (8 test files)
- **커버리지**: 92% stmts / 79% branches / 94% funcs / 98% lines
