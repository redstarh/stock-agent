# 주식 거래 시스템 - Stories & Tasks

> **프로젝트**: Personal Trading System
> **아키텍처**: Modular Monolith (3 Services)
> **기간**: 10주 (70일)
> **팀 구성**: Claude Code Teams

---

## 📊 프로젝트 구조

```
Epics (4개)
  └─ Stories (20개)
      └─ Tasks (85개)
```

---

## 🎯 Epic 목록

| Epic ID | Epic Name | 설명 | 기간 |
|---------|-----------|------|------|
| EPIC-1 | MVP 개발 | 시뮬레이터 거래 시스템 구축 | Week 1-4 |
| EPIC-2 | 실전 거래 연동 | 증권사 API 통합 및 리스크 관리 | Week 5-7 |
| EPIC-3 | 고급 기능 | 분석, 백테스팅, 알림 | Week 8-10 |
| EPIC-4 | 인프라 & 배포 | DevOps, 모니터링, 보안 | Week 1-10 (병행) |

---

## Epic 1: MVP 개발 (시뮬레이터)

### Story 1.1: 개발 환경 설정

**스토리 포인트**: 5
**우선순위**: Highest
**담당 팀**: DevOps Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1001 | 프로젝트 디렉토리 구조 생성 | backend, frontend, market-data, broker-connector 생성 | DevOps Agent | 1h |
| TASK-1002 | Docker Compose 파일 작성 | PostgreSQL, Redis, 3개 서비스 정의 | DevOps Agent | 3h |
| TASK-1003 | 환경 변수 설정 | .env 파일 생성, 비밀키 생성 | DevOps Agent | 1h |
| TASK-1004 | Git 저장소 초기화 | .gitignore, README 작성 | DevOps Agent | 1h |
| TASK-1005 | 로컬 개발 환경 테스트 | docker-compose up 실행 확인 | DevOps Agent | 2h |

**완료 조건 (DoD)**:
- [ ] Docker Compose로 모든 서비스 정상 실행
- [ ] PostgreSQL, Redis 연결 확인
- [ ] 환경 변수 로드 확인

---

### Story 1.2: 데이터베이스 설계 및 구현

**스토리 포인트**: 8
**우선순위**: Highest
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1101 | ERD 설계 | users, accounts, orders, positions 등 설계 | Backend Developer | 3h |
| TASK-1102 | SQLAlchemy 모델 작성 | ORM 모델 구현 | Backend Developer | 4h |
| TASK-1103 | Alembic 마이그레이션 설정 | DB 마이그레이션 환경 구축 | Backend Developer | 2h |
| TASK-1104 | 초기 마이그레이션 실행 | 테이블 생성 스크립트 | Backend Developer | 1h |
| TASK-1105 | 시드 데이터 작성 | 테스트용 더미 데이터 | Backend Developer | 2h |
| TASK-1106 | 인덱스 최적화 | 성능 향상을 위한 인덱스 추가 | Backend Developer | 2h |

**완료 조건 (DoD)**:
- [ ] 모든 테이블 정상 생성
- [ ] 마이그레이션 rollback 가능
- [ ] 시드 데이터 정상 입력
- [ ] 외래키 제약 조건 동작 확인

---

### Story 1.3: 사용자 인증 시스템

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1201 | 사용자 모델 구현 | User 엔티티 및 비즈니스 로직 | Backend Developer | 3h |
| TASK-1202 | 회원가입 API | POST /api/auth/register | Backend Developer | 3h |
| TASK-1203 | 로그인 API | POST /api/auth/login, JWT 발급 | Backend Developer | 4h |
| TASK-1204 | JWT 미들웨어 | 토큰 검증 및 인가 | Backend Developer | 3h |
| TASK-1205 | 로그아웃 API | 토큰 무효화 | Backend Developer | 2h |
| TASK-1206 | 비밀번호 재설정 | 이메일 인증 기반 재설정 | Backend Developer | 4h |
| TASK-1207 | 2FA 구현 (선택) | TOTP 기반 2단계 인증 | Backend Developer | 5h |

**완료 조건 (DoD)**:
- [ ] 회원가입/로그인 정상 동작
- [ ] JWT 토큰 발급 및 검증
- [ ] 인증 실패 시 적절한 에러 응답
- [ ] 단위 테스트 작성 (커버리지 80%)

---

### Story 1.4: 계좌 관리 시스템

**스토리 포인트**: 5
**우선순위**: High
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1301 | 계좌 모델 구현 | Account 엔티티 (시뮬레이터/실전 구분) | Backend Developer | 2h |
| TASK-1302 | 계좌 생성 API | POST /api/accounts | Backend Developer | 3h |
| TASK-1303 | 계좌 목록 조회 | GET /api/accounts | Backend Developer | 2h |
| TASK-1304 | 잔고 조회 API | GET /api/accounts/:id/balance | Backend Developer | 2h |
| TASK-1305 | 입금 처리 | POST /api/accounts/:id/deposit | Backend Developer | 3h |
| TASK-1306 | 출금 처리 | POST /api/accounts/:id/withdraw | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 계좌 생성 및 조회 가능
- [ ] 입출금 트랜잭션 정상 처리
- [ ] 잔고 부족 시 출금 거부
- [ ] 거래 내역 기록

---

### Story 1.5: 주문 처리 시스템

**스토리 포인트**: 13
**우선순위**: Highest
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1401 | Order 모델 구현 | 주문 엔티티 및 상태 머신 | Backend Developer | 4h |
| TASK-1402 | 시뮬레이터 엔진 구현 | 가상 체결 로직 | Backend Developer | 8h |
| TASK-1403 | 주문 생성 API | POST /api/orders | Backend Developer | 4h |
| TASK-1404 | 주문 취소 API | DELETE /api/orders/:id | Backend Developer | 3h |
| TASK-1405 | 주문 목록 조회 | GET /api/orders | Backend Developer | 2h |
| TASK-1406 | 주문 검증 로직 | 잔고, 수량, 가격 검증 | Backend Developer | 4h |
| TASK-1407 | 체결 처리 로직 | Execution 생성, 포지션 업데이트 | Backend Developer | 5h |
| TASK-1408 | 주문 상태 추적 | 상태 변경 이벤트 로깅 | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 시장가/지정가 주문 처리
- [ ] 체결 시 잔고/포지션 자동 업데이트
- [ ] 미체결 주문 취소 가능
- [ ] 주문 이력 조회 가능

---

### Story 1.6: 포트폴리오 관리

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1501 | Position 모델 구현 | 보유 종목 엔티티 | Backend Developer | 3h |
| TASK-1502 | 포트폴리오 조회 API | GET /api/portfolio | Backend Developer | 3h |
| TASK-1503 | 보유 종목 상세 | GET /api/portfolio/positions | Backend Developer | 2h |
| TASK-1504 | 평가 손익 계산 | 실시간 가격 기반 손익 계산 | Backend Developer | 4h |
| TASK-1505 | 수익률 계산 | ROI, 총 수익률 계산 | Backend Developer | 3h |
| TASK-1506 | 자산 배분 분석 | 종목별 비중 계산 | Backend Developer | 2h |

**완료 조건 (DoD)**:
- [ ] 보유 종목 목록 조회
- [ ] 평가액, 손익, 수익률 정확히 계산
- [ ] 실시간 가격 반영
- [ ] 자산 배분 비율 표시

---

### Story 1.7: Market Data Service 개발

**스토리 포인트**: 13
**우선순위**: High
**담당 팀**: Data Engineer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1601 | 프로젝트 초기화 | Python/Go 프로젝트 설정 | Data Engineer | 2h |
| TASK-1602 | Yahoo Finance API 연동 | yfinance 라이브러리 통합 | Data Engineer | 4h |
| TASK-1603 | Alpha Vantage 연동 | 실시간 시세 API | Data Engineer | 4h |
| TASK-1604 | 데이터 정규화 | 통합 데이터 포맷 정의 | Data Engineer | 3h |
| TASK-1605 | Redis 캐싱 구현 | 시세 데이터 캐싱 (TTL 5초) | Data Engineer | 3h |
| TASK-1606 | REST API 구현 | GET /quote/:symbol 등 | Data Engineer | 4h |
| TASK-1607 | WebSocket 서버 구현 | 실시간 스트리밍 | Data Engineer | 8h |
| TASK-1608 | 구독 관리 시스템 | 클라이언트별 심볼 구독 관리 | Data Engineer | 4h |
| TASK-1609 | 에러 핸들링 | API 실패 시 재시도 로직 | Data Engineer | 3h |

**완료 조건 (DoD)**:
- [ ] REST API로 현재가 조회
- [ ] WebSocket으로 실시간 시세 수신
- [ ] 외부 API 장애 시 캐시 사용
- [ ] 최소 100개 동시 연결 지원

---

### Story 1.8: Frontend - 기본 구조

**스토리 포인트**: 8
**우선순위**: Medium
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1701 | React 프로젝트 생성 | Vite + TypeScript 설정 | Frontend Developer | 2h |
| TASK-1702 | 라우팅 설정 | React Router 설정 | Frontend Developer | 2h |
| TASK-1703 | 상태 관리 설정 | Zustand 설정 | Frontend Developer | 2h |
| TASK-1704 | API 클라이언트 구현 | Axios + TanStack Query | Frontend Developer | 4h |
| TASK-1705 | 인증 컨텍스트 | JWT 토큰 관리 | Frontend Developer | 3h |
| TASK-1706 | TailwindCSS 설정 | 스타일 시스템 구축 | Frontend Developer | 2h |
| TASK-1707 | 공통 컴포넌트 | Button, Input, Card 등 | Frontend Developer | 5h |

**완료 조건 (DoD)**:
- [ ] 프로젝트 빌드 성공
- [ ] 라우팅 정상 동작
- [ ] API 호출 및 에러 처리
- [ ] 공통 컴포넌트 Storybook 문서화

---

### Story 1.9: Frontend - 인증 화면

**스토리 포인트**: 5
**우선순위**: High
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1801 | 로그인 페이지 | 이메일/비밀번호 폼 | Frontend Developer | 3h |
| TASK-1802 | 회원가입 페이지 | 사용자 정보 입력 폼 | Frontend Developer | 4h |
| TASK-1803 | 폼 검증 | React Hook Form + Zod | Frontend Developer | 3h |
| TASK-1804 | 인증 플로우 연동 | API 연동 및 토큰 저장 | Frontend Developer | 3h |
| TASK-1805 | Protected Route | 인증 필요 페이지 보호 | Frontend Developer | 2h |

**완료 조건 (DoD)**:
- [ ] 로그인/회원가입 정상 동작
- [ ] 폼 검증 메시지 표시
- [ ] 로그인 성공 시 대시보드 이동
- [ ] 미인증 접근 시 로그인 페이지로 리다이렉트

---

### Story 1.10: Frontend - 주문 화면

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-1901 | 주문 폼 컴포넌트 | 종목, 수량, 가격 입력 | Frontend Developer | 4h |
| TASK-1902 | 주문 타입 선택 | 시장가/지정가 토글 | Frontend Developer | 2h |
| TASK-1903 | 매수/매도 버튼 | 주문 제출 로직 | Frontend Developer | 3h |
| TASK-1904 | 주문 확인 모달 | 주문 내용 확인 팝업 | Frontend Developer | 3h |
| TASK-1905 | 주문 내역 테이블 | 과거 주문 목록 표시 | Frontend Developer | 4h |
| TASK-1906 | 실시간 주문 상태 | WebSocket으로 상태 업데이트 | Frontend Developer | 4h |

**완료 조건 (DoD)**:
- [ ] 주문 폼 입력 및 검증
- [ ] 주문 제출 성공/실패 처리
- [ ] 주문 내역 페이징 처리
- [ ] 미체결 주문 취소 가능

---

### Story 1.11: Frontend - 포트폴리오 화면

**스토리 포인트**: 8
**우선순위**: Medium
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2001 | 포트폴리오 요약 카드 | 총 자산, 수익률 표시 | Frontend Developer | 3h |
| TASK-2002 | 보유 종목 테이블 | 종목별 수량, 평가액, 손익 | Frontend Developer | 4h |
| TASK-2003 | 자산 배분 차트 | Pie Chart (Recharts) | Frontend Developer | 4h |
| TASK-2004 | 수익률 그래프 | Line Chart (일별 수익률) | Frontend Developer | 5h |
| TASK-2005 | 실시간 평가액 업데이트 | WebSocket 시세 반영 | Frontend Developer | 4h |

**완료 조건 (DoD)**:
- [ ] 포트폴리오 데이터 정상 표시
- [ ] 차트 인터랙션 동작
- [ ] 실시간 가격 반영
- [ ] 반응형 디자인 적용

---

### Story 1.12: Frontend - 차트 및 시세

**스토리 포인트**: 8
**우선순위**: Medium
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2101 | 주식 검색 컴포넌트 | 종목 자동완성 | Frontend Developer | 4h |
| TASK-2102 | 가격 차트 컴포넌트 | Candlestick 차트 | Frontend Developer | 6h |
| TASK-2103 | 호가창 컴포넌트 | 매수/매도 호가 표시 | Frontend Developer | 4h |
| TASK-2104 | 실시간 시세 표시 | WebSocket 연결 및 업데이트 | Frontend Developer | 4h |
| TASK-2105 | 차트 인터랙션 | 줌, 팬, 툴팁 | Frontend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 종목 검색 및 선택
- [ ] 가격 차트 정상 표시
- [ ] 실시간 시세 업데이트
- [ ] 모바일 반응형

---

## Epic 2: 실전 거래 연동

### Story 2.1: Broker Connector Service 구축

**스토리 포인트**: 13
**우선순위**: Highest
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2201 | 프로젝트 초기화 | Python FastAPI 프로젝트 | Backend Developer | 2h |
| TASK-2202 | Broker 인터페이스 정의 | 추상 클래스 설계 | Backend Developer | 3h |
| TASK-2203 | 키움증권 연동 | PyKiwoom 통합 | Backend Developer | 8h |
| TASK-2204 | 계좌 연결 API | POST /broker/connect | Backend Developer | 4h |
| TASK-2205 | 주문 전송 API | POST /broker/order | Backend Developer | 5h |
| TASK-2206 | 계좌 동기화 | GET /broker/sync | Backend Developer | 4h |
| TASK-2207 | 체결 수신 로직 | 증권사 콜백 처리 | Backend Developer | 6h |
| TASK-2208 | API Key 암호화 저장 | AES-256 암호화 | Backend Developer | 4h |

**완료 조건 (DoD)**:
- [ ] 증권사 계정 연결 성공
- [ ] 테스트 주문 전송 및 체결 확인
- [ ] API Key 안전하게 저장
- [ ] 연결 실패 시 에러 처리

---

### Story 2.2: Trading Abstraction Layer

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2301 | ITradingEngine 인터페이스 | 공통 인터페이스 정의 | Backend Developer | 3h |
| TASK-2302 | SimulatorEngine 구현 | 기존 시뮬레이터 래핑 | Backend Developer | 4h |
| TASK-2303 | LiveTradingEngine 구현 | Broker Connector 래핑 | Backend Developer | 4h |
| TASK-2304 | 주문 라우팅 로직 | 모드별 엔진 선택 | Backend Developer | 3h |
| TASK-2305 | 모드 전환 API | POST /api/trading/switch-mode | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 시뮬레이터/실전 모드 전환 가능
- [ ] 동일 API로 양쪽 모드 사용
- [ ] 모드별 주문 정상 처리
- [ ] 전환 시 경고 메시지

---

### Story 2.3: 리스크 관리 시스템

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2401 | 리스크 한도 모델 | RiskLimit 엔티티 | Backend Developer | 2h |
| TASK-2402 | 한도 설정 API | PUT /api/risk/limits | Backend Developer | 3h |
| TASK-2403 | 주문 전 검증 | 잔고, 한도, 포지션 검증 | Backend Developer | 5h |
| TASK-2404 | Circuit Breaker | 일일 손실 한도 초과 시 차단 | Backend Developer | 4h |
| TASK-2405 | 리스크 알림 | 한도 근접 시 경고 | Backend Developer | 3h |
| TASK-2406 | 리스크 대시보드 API | GET /api/risk/exposure | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 리스크 한도 설정 가능
- [ ] 한도 초과 시 주문 거부
- [ ] 일일 손실 한도 동작
- [ ] 리스크 현황 조회

---

### Story 2.4: Frontend - 실전 거래 UI

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-2501 | 증권사 연결 페이지 | API Key 입력 폼 | Frontend Developer | 4h |
| TASK-2502 | 모드 전환 스위치 | 시뮬레이터 ↔ 실전 토글 | Frontend Developer | 3h |
| TASK-2503 | 실전 주문 확인 모달 | 추가 확인 단계 | Frontend Developer | 3h |
| TASK-2504 | 리스크 한도 설정 화면 | 한도 입력 및 저장 | Frontend Developer | 4h |
| TASK-2505 | 리스크 대시보드 | 현재 노출도 표시 | Frontend Developer | 4h |
| TASK-2506 | 경고 알림 UI | 리스크 경고 토스트 | Frontend Developer | 2h |

**완료 조건 (DoD)**:
- [ ] 증권사 연결 플로우 완료
- [ ] 모드 전환 시 명확한 표시
- [ ] 실전 주문 시 추가 확인
- [ ] 리스크 한도 설정 가능

---

## Epic 3: 고급 기능

### Story 3.1: 성과 분석 시스템

**스토리 포인트**: 8
**우선순위**: Medium
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-3001 | 성과 지표 계산 | Sharpe Ratio, MDD 등 | Backend Developer | 5h |
| TASK-3002 | 일별 수익률 API | GET /api/analytics/daily-returns | Backend Developer | 3h |
| TASK-3003 | 월간 리포트 생성 | PDF 리포트 생성 | Backend Developer | 5h |
| TASK-3004 | 거래 통계 API | 승률, 평균 수익/손실 | Backend Developer | 4h |
| TASK-3005 | 종목별 성과 분석 | 종목별 수익률 랭킹 | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 성과 지표 정확히 계산
- [ ] 리포트 PDF 생성
- [ ] 거래 통계 조회 가능
- [ ] 종목별 성과 비교

---

### Story 3.2: 백테스팅 엔진

**스토리 포인트**: 13
**우선순위**: Medium
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-3101 | 과거 데이터 로드 | Market Data에서 historical 데이터 | Backend Developer | 4h |
| TASK-3102 | 전략 인터페이스 정의 | 사용자 정의 전략 구조 | Backend Developer | 4h |
| TASK-3103 | 백테스트 실행 엔진 | 과거 데이터로 시뮬레이션 | Backend Developer | 8h |
| TASK-3104 | 성과 계산 | 수익률, Sharpe, MDD | Backend Developer | 4h |
| TASK-3105 | 백테스트 결과 저장 | Report 모델 및 저장 | Backend Developer | 3h |
| TASK-3106 | 백테스트 API | POST /api/analytics/backtest | Backend Developer | 4h |

**완료 조건 (DoD)**:
- [ ] 간단한 전략 백테스트 실행
- [ ] 과거 데이터로 정확한 시뮬레이션
- [ ] 성과 지표 계산
- [ ] 결과 저장 및 조회

---

### Story 3.3: 알림 시스템

**스토리 포인트**: 5
**우선순위**: Low
**담당 팀**: Backend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-3201 | Alert 모델 구현 | 가격 알림 설정 | Backend Developer | 2h |
| TASK-3202 | 알림 설정 API | POST /api/alerts | Backend Developer | 3h |
| TASK-3203 | 가격 모니터링 | 실시간 가격 체크 (Celery) | Backend Developer | 5h |
| TASK-3204 | 이메일 발송 | SendGrid 연동 | Backend Developer | 4h |
| TASK-3205 | WebSocket 알림 | 실시간 브라우저 알림 | Backend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 가격 알림 설정 가능
- [ ] 목표가 도달 시 이메일 발송
- [ ] 실시간 브라우저 알림
- [ ] 알림 내역 조회

---

### Story 3.4: Frontend - 분석 & 백테스팅

**스토리 포인트**: 8
**우선순위**: Medium
**담당 팀**: Frontend Developer Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-3301 | 성과 대시보드 | 지표 카드, 차트 | Frontend Developer | 5h |
| TASK-3302 | 백테스팅 폼 | 전략 입력 인터페이스 | Frontend Developer | 5h |
| TASK-3303 | 백테스트 결과 표시 | 수익률 차트, 거래 로그 | Frontend Developer | 5h |
| TASK-3304 | 거래 통계 페이지 | 승률, 평균 손익 | Frontend Developer | 4h |
| TASK-3305 | 알림 설정 페이지 | 가격 알림 추가/삭제 | Frontend Developer | 3h |

**완료 조건 (DoD)**:
- [ ] 성과 지표 시각화
- [ ] 백테스트 실행 및 결과 표시
- [ ] 거래 통계 조회
- [ ] 알림 설정 UI

---

## Epic 4: 인프라 & 배포

### Story 4.1: CI/CD 파이프라인

**스토리 포인트**: 5
**우선순위**: Medium
**담당 팀**: DevOps Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-4001 | GitHub Actions 워크플로우 | .github/workflows/ 설정 | DevOps Agent | 3h |
| TASK-4002 | 자동 테스트 실행 | pytest, jest 실행 | DevOps Agent | 2h |
| TASK-4003 | Docker 이미지 빌드 | 서비스별 이미지 빌드 | DevOps Agent | 3h |
| TASK-4004 | 이미지 레지스트리 푸시 | Docker Hub/GHCR | DevOps Agent | 2h |
| TASK-4005 | 배포 스크립트 | SSH로 서버 배포 | DevOps Agent | 4h |

**완료 조건 (DoD)**:
- [ ] Push 시 자동 테스트
- [ ] 테스트 통과 시 자동 빌드
- [ ] 프로덕션 배포 자동화
- [ ] 배포 실패 시 롤백

---

### Story 4.2: 모니터링 & 로깅

**스토리 포인트**: 5
**우선순위**: Medium
**담당 팀**: DevOps Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-4101 | 로깅 설정 | 구조화된 로그 (JSON) | DevOps Agent | 3h |
| TASK-4102 | 헬스 체크 엔드포인트 | GET /health, /ready | DevOps Agent | 2h |
| TASK-4103 | Uptime 모니터링 | UptimeRobot 설정 | DevOps Agent | 1h |
| TASK-4104 | 에러 추적 | Sentry 통합 | DevOps Agent | 3h |
| TASK-4105 | 로그 수집 | Docker logs → 파일 | DevOps Agent | 2h |

**완료 조건 (DoD)**:
- [ ] 구조화된 로그 출력
- [ ] 헬스 체크 동작
- [ ] Uptime 알림 설정
- [ ] 에러 발생 시 Sentry 알림

---

### Story 4.3: 보안 강화

**스토리 포인트**: 5
**우선순위**: High
**담당 팀**: Security & Compliance Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-4201 | HTTPS 설정 | Let's Encrypt SSL | DevOps Agent | 2h |
| TASK-4202 | API Rate Limiting | 요청 제한 미들웨어 | Backend Developer | 3h |
| TASK-4203 | CORS 설정 | 허용 도메인 관리 | Backend Developer | 1h |
| TASK-4204 | SQL Injection 방지 | ORM 사용 검증 | Backend Developer | 2h |
| TASK-4205 | XSS 방지 | 입력 sanitization | Frontend Developer | 2h |
| TASK-4206 | 보안 헤더 설정 | Helmet.js 등 | Backend Developer | 2h |

**완료 조건 (DoD)**:
- [ ] HTTPS 적용
- [ ] Rate Limiting 동작
- [ ] CORS 정상 동작
- [ ] 보안 취약점 패치

---

### Story 4.4: 백업 & 복구

**스토리 포인트**: 3
**우선순위**: Medium
**담당 팀**: DevOps Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-4301 | 백업 스크립트 | PostgreSQL 백업 자동화 | DevOps Agent | 3h |
| TASK-4302 | Cron 설정 | 매일 자동 백업 | DevOps Agent | 1h |
| TASK-4303 | 백업 검증 | 복구 테스트 | DevOps Agent | 2h |
| TASK-4304 | 클라우드 업로드 | S3/GCS 백업 (선택) | DevOps Agent | 3h |

**완료 조건 (DoD)**:
- [ ] 자동 백업 실행
- [ ] 백업 파일 검증
- [ ] 복구 절차 문서화
- [ ] 7일치 백업 유지

---

### Story 4.5: 프로덕션 배포

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: DevOps Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-4401 | VPS 서버 설정 | DigitalOcean/Vultr 설정 | DevOps Agent | 3h |
| TASK-4402 | Docker 설치 | Docker, Docker Compose 설치 | DevOps Agent | 1h |
| TASK-4403 | Nginx 설정 | 리버스 프록시 설정 | DevOps Agent | 3h |
| TASK-4404 | SSL 인증서 | Let's Encrypt 설정 | DevOps Agent | 2h |
| TASK-4405 | 환경 변수 설정 | .env.production 작성 | DevOps Agent | 2h |
| TASK-4406 | 첫 배포 | docker-compose up -d | DevOps Agent | 2h |
| TASK-4407 | 도메인 연결 | DNS 설정 | DevOps Agent | 1h |
| TASK-4408 | 배포 문서 작성 | 운영 가이드 | DevOps Agent | 3h |

**완료 조건 (DoD)**:
- [ ] 프로덕션 서버 정상 구동
- [ ] HTTPS 접속 가능
- [ ] 도메인 연결 완료
- [ ] 배포 문서 작성

---

## Epic 5: 테스트 & 품질 관리

### Story 5.1: 백엔드 테스트

**스토리 포인트**: 8
**우선순위**: High
**담당 팀**: QA/Testing Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-5001 | 단위 테스트 작성 | pytest로 핵심 로직 테스트 | QA/Testing Agent | 8h |
| TASK-5002 | 통합 테스트 | API 엔드포인트 테스트 | QA/Testing Agent | 6h |
| TASK-5003 | 테스트 커버리지 측정 | pytest-cov로 80% 목표 | QA/Testing Agent | 3h |
| TASK-5004 | 주문 플로우 테스트 | E2E 주문 시나리오 | QA/Testing Agent | 5h |

**완료 조건 (DoD)**:
- [ ] 테스트 커버리지 80% 이상
- [ ] 모든 테스트 통과
- [ ] CI에서 자동 실행
- [ ] 테스트 문서 작성

---

### Story 5.2: 프론트엔드 테스트

**스토리 포인트**: 5
**우선순위**: Medium
**담당 팀**: QA/Testing Agent

#### Tasks

| Task ID | Task 제목 | 설명 | 담당자 | 예상 시간 |
|---------|----------|------|--------|----------|
| TASK-5101 | 컴포넌트 테스트 | Jest + React Testing Library | QA/Testing Agent | 5h |
| TASK-5102 | 통합 테스트 | 주요 플로우 테스트 | QA/Testing Agent | 4h |
| TASK-5103 | E2E 테스트 (선택) | Playwright/Cypress | QA/Testing Agent | 6h |

**완료 조건 (DoD)**:
- [ ] 주요 컴포넌트 테스트
- [ ] 로그인 플로우 테스트
- [ ] 주문 플로우 테스트

---

## 📊 전체 스토리 요약

| Epic | Stories | Tasks | Story Points | 예상 기간 |
|------|---------|-------|--------------|----------|
| EPIC-1: MVP 개발 | 12 | 60 | 96 | 4주 |
| EPIC-2: 실전 거래 연동 | 4 | 22 | 37 | 3주 |
| EPIC-3: 고급 기능 | 4 | 20 | 34 | 3주 |
| EPIC-4: 인프라 & 배포 | 5 | 22 | 26 | 병행 |
| EPIC-5: 테스트 | 2 | 7 | 13 | 병행 |
| **Total** | **27** | **131** | **206** | **10주** |

---

## 🎯 Sprint 계획 (2주 스프린트)

### Sprint 1 (Week 1-2): 기반 구축
- Story 1.1: 개발 환경 설정
- Story 1.2: 데이터베이스 설계
- Story 1.3: 사용자 인증
- Story 4.1: CI/CD (병행)

### Sprint 2 (Week 3-4): 핵심 거래 기능
- Story 1.4: 계좌 관리
- Story 1.5: 주문 처리
- Story 1.6: 포트폴리오
- Story 1.7: Market Data Service

### Sprint 3 (Week 5-6): 프론트엔드 MVP
- Story 1.8: Frontend 기본 구조
- Story 1.9: 인증 화면
- Story 1.10: 주문 화면
- Story 1.11: 포트폴리오 화면
- Story 1.12: 차트

### Sprint 4 (Week 7-8): 실전 거래
- Story 2.1: Broker Connector
- Story 2.2: Trading Abstraction
- Story 2.3: 리스크 관리
- Story 2.4: Frontend 실전 UI

### Sprint 5 (Week 9-10): 고급 기능 & 배포
- Story 3.1: 성과 분석
- Story 3.2: 백테스팅
- Story 3.3: 알림
- Story 3.4: Frontend 분석
- Story 4.5: 프로덕션 배포

---

## 팀 역할 매핑

| Role | Claude Agent | 주요 책임 | Stories |
|------|-------------|----------|---------|
| Backend Lead | Backend Developer Agent | API, 비즈니스 로직 | 15 stories |
| Frontend Lead | Frontend Developer Agent | UI/UX 개발 | 6 stories |
| Data Engineer | Data Engineer Agent | 시장 데이터 | 1 story |
| DevOps | DevOps Agent | 인프라, 배포 | 4 stories |
| QA | QA/Testing Agent | 테스트, 품질 | 2 stories |

---

## 다음 단계

1. **Jira 등록**: Excel 파일을 Jira로 import
2. **Sprint 계획**: Story를 Sprint에 할당
3. **팀 배정**: Agent별 Story 할당
4. **킥오프**: 개발 시작

---

**문서 버전**: 1.0
**작성일**: 2026-02-07
**다음 업데이트**: Sprint 1 시작 시
