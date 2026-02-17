# Task [6] Backend: REST API 서버 — 오류 기록

## ERR-6-1: lifespan 이벤트 미실행 (ASGITransport)

- **증상**: `sqlite3.OperationalError: no such table: news_event` — 통합 테스트에서 모든 API 엔드포인트 실패
- **원인**: `httpx.ASGITransport`로 테스트 시 FastAPI의 `lifespan` 컨텍스트 매니저가 실행되지 않아 `Base.metadata.create_all()` 호출 안됨
- **수정**: `tests/integration/conftest.py` 생성 — 테스트 전용 SQLite in-memory 엔진 + `app.dependency_overrides[get_db]` 오버라이드
- **영향 파일**: `tests/integration/conftest.py` (신규)

## ERR-6-2: `app` 모듈/인스턴스 이름 충돌

- **증상**: `AttributeError: module 'app' has no attribute 'dependency_overrides'`
- **원인**: `from app.main import app` 시 Python 패키지 `app`과 FastAPI 인스턴스 `app`이 네이밍 충돌. conftest에서 `app.dependency_overrides` 접근 시 패키지 모듈로 해석됨
- **수정**: `from app.main import app as fastapi_app` 별칭 사용
- **영향 파일**: `tests/integration/conftest.py`

## 최종 결과

- **테스트**: 52 passed (unit 28 + integration 24)
- **커버리지**: 94.49%
- **미커버 라인**: `app/api/news.py:25-36` (DB에 데이터 있을 때 score 계산 분기), `app/main.py:21-22,49` (lifespan + exception handler)
