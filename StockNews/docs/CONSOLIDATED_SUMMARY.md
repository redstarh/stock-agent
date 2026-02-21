# StockNews — Consolidated PRD / Architecture / Status Summary

요약(한줄): StockNews는 KR/US 뉴스 수집 → 전처리 → LLM/NLP 분석 → 점수화 → REST/Redis로 제공하는 뉴스 인텔리전스 서비스입니다.

1) 제품(가치) 요약 (PRD 요점)
- 대상: 트레이딩 시스템(StockAgent), 투자분석가, 프론트엔드 대시보드 사용자
- 주요 기능: 실시간 고영향(breaking) 뉴스 알림, 종목별 뉴스 점수·타임라인, 테마 강도 순위, 예측 검증 엔진
- SLAs/목표: 응답(캐시) <200ms, 브레이킹 뉴스 지연 <1s(캐시/네트워크 영향 제외)

2) 현재 개발/배포 상태
- Phase 1..3 완료로 문서에 표시(백엔드/프론트엔드 테스트 통과 보고 있음). 구현 파일: `backend/app/` 및 `frontend/src/`
- 핵심 구현: Redis Pub/Sub → WebSocket 브로드캐스트, Scoring Engine(Recency/Frequency/Sentiment/Disclosure 가중치), Verification Engine

3) 아키텍처(요점)
- 입력: 외부 소스(Naver, DART, Finnhub, NewsAPI)
- 파이프라인: Collector → Dedup → NLP/LLM 분석(요약·감성·종목 매핑) → Scoring → DB → REST/WS/Redis
- 인프라: FastAPI, PostgreSQL/SQLite, Redis, Vite+React, LLM API
- 통합 포인트: REST API(`GET /api/v1/news/score`) 및 Redis 채널 `breaking_news` (score >= 80)

4) 주요 API / DB / 메시지 계약
- REST: `/news/score`, `/news/top`, `/news/latest`, `/stocks/{code}/timeline`, `/theme/strength`, `/health`
- Redis: 채널 `news_breaking_kr`, `news_breaking_us` (JSON payload — stock_code, title, score, sentiment, market, published_at)
- DB: `news_event`, `theme_strength`, 검증 엔진용 `DailyPredictionResult`, `ThemePredictionAccuracy` 등

5) 문서·테스트 현황
- 문서 위치: `docs/`에 아키텍처·스펙·테스크플랜 존재 (`StockNews-v1.0.md`, `MLPipeline-Spec.md`, `PredictionVerification-Spec.md`, 등)
- 테스트: 백엔드/프론트엔드 유닛/통합 테스트가 준비되어 있으며, 관련 테스트 파일이 `backend/tests/` 및 `frontend/tests/`에 존재

6) 권장 정리(비파괴, 우선순위)
1. 우선: 문서 보관 제안(`docs/err/*`)을 아카이브 폴더로 이동 — 코드 영향 없음. (사용자 승인 필요)
2. 문서 정합성 검토: `StockNews-v1.0.md`를 공식 시스템 설계서로 삼고, 중복/구버전 문서는 참조 링크로 통합
3. README/CLAUDE.md 정리: 핵심 엔드포인트·계약을 `shared/contracts/`와 교차검증하여 유지
4. (선택) `docs/` 폴더 구조 정리 제안: `docs/specs/`, `docs/arch/`, `docs/plans/`, `docs/archived/`

7) 위험/주의사항
- 문서 이동·삭제는 코드 실행에 영향을 주지 않지만, CI나 자동 스크립트에서 문서를 참조하는 경우(예: 자동 릴리즈 체크) 참조 경로를 업데이트해야 합니다. 따라서 삭제 전 grep으로 참조 확인 권장.

8) 다음 단계 제안
- 제가 제안한 보관 목록(`ARCHIVE_CANDIDATES.md`)을 승인해 주세요. 승인 시 파일을 `docs/archived/`로 이동하고 PR을 만들겠습니다.
- 원하시면 `docs/` 재구조화(폴더 이동 + README 업데이트)도 진행하겠습니다.
