# Task [7] Backend: WebSocket 서버 — 오류 기록

## 오류 없음

Task [7]은 TDD 사이클 과정에서 오류 없이 완료됨.

## 참고 사항

- fakeredis DeprecationWarning 12건 (retry_on_timeout, lib_name, lib_version) — 기능에 영향 없음
- `websocket.py` 커버리지 67%: broadcast(), _add_connection() 거부 경로, disconnect/error 핸들링 브랜치 미커버
  - 이들은 실제 동시 연결 시나리오에서만 테스트 가능 (E2E에서 보완 예정)

## 구현 요약

- **pubsub.py**: Redis Pub/Sub 속보 발행 (score >= 80 임계값), 마켓별 채널 분리
- **websocket.py**: WS /ws/news 엔드포인트, 연결 관리, ping/pong, 최대 100 동시 연결

## 최종 결과

- **테스트**: 116 passed (전체), Task [7] 9 passed (pubsub 5 + websocket 4)
- **커버리지**: 91.07% (전체), pubsub 84%, websocket 67%
