# Sprint 0 - F-2 에러 기록

## [에러 1] jest-environment-jsdom에 fetch/Response 미포함
- **단계**: RED (테스트 실행)
- **에러**: `ReferenceError: Response is not defined` — MSW가 fetch API globals를 필요로 하나 jsdom에 없음
- **원인**: jest-environment-jsdom이 Node.js 네이티브 fetch globals를 제거함
- **해결**: API 클라이언트 테스트에 `@jest-environment node` docblock 추가 (DOM 불필요)

## [에러 2] MSW ESM 모듈 변환 실패
- **단계**: RED (테스트 실행)
- **에러**: `SyntaxError: Unexpected token 'export'` — msw/until-async가 ESM인데 Jest가 CJS로 처리
- **원인**: next/jest가 transformIgnorePatterns를 자체 값으로 덮어씀
- **해결**: `createJestConfig` 결과를 async 함수로 감싸서 resolved config의 transformIgnorePatterns를 직접 패치
  ```typescript
  const jestConfig = async () => {
    const resolved = await createJestConfig(config)();
    resolved.transformIgnorePatterns = [
      "node_modules/(?!(msw|@mswjs|until-async)/)",
    ];
    return resolved;
  };
  ```

## 최종 결과
- 테스트 5/5 통과 (health, balance, positions, 500 error, network error)
- 전체 Frontend 테스트 8/8 통과 (T-F1 3개 + T-F2 5개)
