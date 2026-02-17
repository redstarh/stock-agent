# Task [2] Backend: DB 모델 + 설정 — 발견된 오류

## ERR-1: SQLite timezone 미지원
- **위치**: `tests/unit/test_models.py::test_news_event_has_published_at`
- **증상**: `datetime(2026, ...) != datetime(2026, ..., tzinfo=utc)` — timezone 비교 실패
- **원인**: SQLite는 `DateTime(timezone=True)`를 저장해도 timezone 정보를 유지하지 않음
- **수정**: 테스트에서 `.replace(tzinfo=None)`으로 naive datetime 비교
- **상태**: ✅ 수정 완료
- **참고**: PostgreSQL 전환 시 이 제한이 해소됨. Production에서는 문제 없음

## ERR-2: conftest.py transaction rollback 경고
- **위치**: `tests/conftest.py:35`
- **증상**: `SAWarning: transaction already deassociated from connection`
- **원인**: IntegrityError 테스트에서 이미 롤백된 트랜잭션에 다시 rollback 시도
- **수정**: `if transaction.is_active:` 조건 추가
- **상태**: ✅ 수정 완료

## ERR-3: 초기 커버리지 부족 (73%)
- **위치**: `app/core/database.py`, `app/core/logger.py`, `app/core/redis.py`
- **증상**: 커버리지 73% (목표 80% 미달)
- **원인**: 인프라 모듈에 대한 테스트 미작성
- **수정**: `tests/unit/test_core.py` 추가 (import + 기본 동작 테스트 7건)
- **상태**: ✅ 수정 완료 (최종 커버리지 96.67%)
