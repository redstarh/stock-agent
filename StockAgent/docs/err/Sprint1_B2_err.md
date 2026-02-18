# Sprint 1 - B-2 에러 기록

## [에러 1] Pydantic 스키마 validation 누락
- **단계**: GREEN (테스트 실행)
- **에러**: `test_trade_log_schema_rejects_invalid` 실패 — `entry_price=-1`, `stock_code=""` 등 유효하지 않은 데이터가 ValidationError 없이 통과
- **원인**: TradeLogResponse 스키마에 `Field` 제약 조건이 없었음
- **해결**: `Field(..., ge=0)`, `Field(..., min_length=1)`, `Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")` 추가

## 최종 결과
- DB 모델 테스트 6/6 통과
- 스키마 테스트 5/5 통과
- 총 11/11 통과
