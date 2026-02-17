# Stock Agent

개인용 주식 거래 시스템 - 시뮬레이터 및 실전 거래 지원

## 프로젝트 개요

이 프로젝트는 주식 투자 시뮬레이터와 실전 거래를 모두 지원하는 통합 거래 플랫폼입니다.

### 주요 기능

- ✅ **시뮬레이터 모드**: 가상 자금으로 주식 거래 연습
- ✅ **실전 거래 모드**: 증권사 API 연동을 통한 실제 거래
- ✅ **포트폴리오 관리**: 실시간 평가액, 손익 계산
- ✅ **리스크 관리**: 일일 손실 한도, 포지션 크기 제한
- ✅ **백테스팅**: 과거 데이터로 투자 전략 검증
- ✅ **실시간 시세**: WebSocket 기반 실시간 가격 업데이트

## 아키텍처

**Modular Monolith** (3 Services)

```
├── Backend API (FastAPI)      # 통합 비즈니스 로직
├── Market Data Service        # 실시간 시세 데이터
└── Broker Connector          # 증권사 API 연동
```

## 기술 스택

### Backend
- **Python 3.11+** (FastAPI)
- **PostgreSQL** (메인 DB)
- **Redis** (캐싱/세션)
- **SQLAlchemy** (ORM)

### Frontend
- **React 18** + **TypeScript**
- **TailwindCSS** (스타일)
- **TanStack Query** (서버 상태)
- **Recharts** (차트)

### 인프라
- **Docker** + **Docker Compose**
- **GitHub Actions** (CI/CD)
- **Nginx** (리버스 프록시)

## 프로젝트 구조

```
AgentDev/
├── backend/                    # FastAPI 백엔드
│   ├── src/
│   │   ├── auth/              # 인증/인가
│   │   ├── trading/           # 주문 처리
│   │   ├── portfolio/         # 포트폴리오
│   │   ├── risk/              # 리스크 관리
│   │   └── analytics/         # 분석/통계
│   └── tests/
│       ├── unit/              # 단위 테스트
│       └── integration/       # 통합 테스트
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── e2e/                   # E2E 테스트
│
├── market-data-service/        # 시장 데이터 서비스
├── broker-connector/          # 증권사 연동 서비스
└── docs/                      # 문서
    ├── personal-trading-system-architecture.md
    ├── TDD.md
    ├── jira_import.md
    └── stories-and-tasks.md
```

## 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd AgentDev

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# Docker Compose로 서비스 시작
docker-compose up -d
```

### 2. 개발 환경

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 테스트 실행
pytest tests/ -v
```

#### Frontend
```bash
cd frontend
npm install

# 개발 서버 시작
npm run dev

# 테스트 실행
npm test
```

## 테스트

### 전체 테스트 실행
```bash
./run-tests.sh all
```

### 백엔드 테스트
```bash
./run-tests.sh backend
```

### 프론트엔드 테스트
```bash
./run-tests.sh frontend
```

### E2E 테스트
```bash
./run-tests.sh e2e
```

### 커버리지 확인
```bash
./run-tests.sh coverage
```

**목표 커버리지**: 80% 이상

## 개발 로드맵

### Phase 1: MVP (4주) ✅
- [x] 개발 환경 설정
- [x] 데이터베이스 설계
- [x] 사용자 인증
- [ ] 계좌 관리
- [ ] 주문 처리
- [ ] 포트폴리오 관리
- [ ] Market Data Service
- [ ] Frontend 기본 UI

### Phase 2: 실전 거래 연동 (3주)
- [ ] Broker Connector 개발
- [ ] Trading Abstraction Layer
- [ ] 리스크 관리 시스템
- [ ] 증권사 API 연동 (키움증권)

### Phase 3: 고급 기능 (3주)
- [ ] 성과 분석
- [ ] 백테스팅 엔진
- [ ] 알림 시스템
- [ ] 차트 고도화

### Phase 4: 배포 (2주)
- [ ] CI/CD 파이프라인
- [ ] 프로덕션 배포
- [ ] 모니터링 시스템
- [ ] 문서 완성

## 문서

- [아키텍처 설계](./personal-trading-system-architecture.md)
- [TDD 가이드](./TDD.md)
- [Jira Import 가이드](./jira_import.md)
- [Stories & Tasks](./stories-and-tasks.md)

## 라이선스

MIT License

## 기여

개인 프로젝트이지만, 제안 사항이 있으시면 이슈를 열어주세요.

## 연락처

- **프로젝트 관리**: [Jira Board](https://stockagent.atlassian.net/jira/software/projects/SCRUM/boards/1)

---

**작성일**: 2026-02-07
**버전**: 1.0.0
**상태**: 개발 중 🚧
