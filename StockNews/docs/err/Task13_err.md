# Task [13] 테스트 인프라 구축 — 발견된 오류

## ERR-1: Vitest globals 타입 미인식
- **위치**: `frontend/tests/smoke.test.tsx`
- **증상**: `Cannot find name 'test'`, `Cannot find name 'expect'` [2582, 2304]
- **원인**: tsconfig에 vitest/globals 타입 미포함
- **수정**: `tsconfig.test.json` 생성, `types: ["vitest/globals", "@testing-library/jest-dom"]` 추가, `tsconfig.json`에 reference 추가
- **상태**: ✅ 수정 완료

## ERR-2: mockStockTimeline 미사용 파라미터 경고
- **위치**: `frontend/tests/mocks/data.ts:67`
- **증상**: `'code' is declared but its value is never read` [6133]
- **원인**: 파라미터명이 `code`로 되어 있으나 실제 사용하지 않음
- **수정**: `_code`로 변경 (unused prefix convention)
- **상태**: ✅ 수정 완료
