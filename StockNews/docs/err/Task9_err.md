# Task 9 — Frontend: 대시보드 페이지 에러 로그

## ERR-9-1: DashboardPage 테스트 — 다중 텍스트 매칭 오류

**증상:**
```
TestingLibraryElementError: Found multiple elements with the text: 삼성전자
```

**원인:**
DashboardPage에서 '삼성전자'가 TopStockCards(종목명)와 NewsList > NewsCard(stock_name span) 두 곳에 렌더링됨.
`screen.getByText('삼성전자')`는 단일 요소만 허용하므로 다중 매칭 시 에러 발생.

**수정:**
`getByText` → `getAllByText`로 변경하고 `.length`로 존재 확인:
```tsx
// Before
expect(screen.getByText('삼성전자')).toBeInTheDocument();

// After
expect(screen.getAllByText('삼성전자').length).toBeGreaterThanOrEqual(1);
```

**영향 파일:** `tests/pages/DashboardPage.test.tsx`

**결과:** 52 tests passed, 94.73% stmts / 80.76% branches / 93.75% funcs / 97.14% lines
