# Task 12 — Frontend: 실시간 알림 에러 로그

## ERR-12-1: WebSocket mock — read-only property 오류

**증상:**
```
TypeError: Cannot assign to read only property 'WebSocket' of object '#<Object>'
```

**원인:**
jsdom 환경에서 `globalThis.WebSocket`은 read-only property로 설정됨.
직접 할당(`globalThis.WebSocket = MockWebSocket`)이 불가능.

**수정:**
`vi.stubGlobal`을 사용하여 Vitest의 공식 global mock API로 교체:
```typescript
// Before
globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// After
vi.stubGlobal('WebSocket', MockWebSocket);
```

`afterEach`에서도 `vi.unstubAllGlobals()`로 정리.

**영향 파일:** `tests/hooks/useWebSocket.test.ts`

**결과:** 85 tests passed, 94.3% stmts / 80.37% branches / 91.04% funcs / 95.91% lines
