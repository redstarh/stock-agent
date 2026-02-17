# 개인용 주식 거래 시스템 아키텍처

> **설계 철학**: 심플하고, 유지보수 쉽고, 비용 효율적인 개인 거래 시스템

---

## 📋 목차
1. [아키텍처 개요](#아키텍처-개요)
2. [시스템 구성](#시스템-구성)
3. [기술 스택](#기술-스택)
4. [데이터베이스 설계](#데이터베이스-설계)
5. [배포 전략](#배포-전략)
6. [개발 로드맵](#개발-로드맵)
7. [비용 분석](#비용-분석)

---

## 아키텍처 개요

### 설계 원칙

```yaml
simplicity:
  - 최소한의 서비스 분리
  - 단일 데이터베이스
  - Docker Compose로 관리

maintainability:
  - 모놀리식 + 모듈화
  - 명확한 레이어 분리
  - 표준 기술 스택

cost_efficiency:
  - 저렴한 VPS 호스팅 가능
  - 무료 티어 활용
  - 최소 인프라
```

---

### 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                         │
│                                                          │
│  ┌──────────────────┐        ┌──────────────────┐      │
│  │   Web Frontend   │        │   Mobile (PWA)   │      │
│  │   (React SPA)    │        │   (Optional)     │      │
│  └──────────────────┘        └──────────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS/WSS
┌────────────────────────▼────────────────────────────────┐
│                Application Layer                         │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Backend API (FastAPI/NestJS)            │   │
│  │                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │  │  Auth    │  │ Trading  │  │Portfolio │     │   │
│  │  │  Module  │  │  Module  │  │ Module   │     │   │
│  │  └──────────┘  └──────────┘  └──────────┘     │   │
│  │                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │  │  Risk    │  │Analytics │  │  Notify  │     │   │
│  │  │  Module  │  │  Module  │  │  Module  │     │   │
│  │  └──────────┘  └──────────┘  └──────────┘     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────┐        ┌──────────────────┐      │
│  │  Market Data Svc │        │ Broker Connector │      │
│  │  (Go/Python)     │        │   (Python)       │      │
│  │  - 실시간 시세    │        │   - 증권사 API   │      │
│  │  - WebSocket     │        │   - 주문 전송    │      │
│  └──────────────────┘        └──────────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Data Layer                             │
│                                                          │
│  ┌──────────────────┐        ┌──────────────────┐      │
│  │   PostgreSQL     │        │   Redis Cache    │      │
│  │   - 단일 DB      │        │   - 세션         │      │
│  │   - 모든 데이터  │        │   - 실시간 시세  │      │
│  └──────────────────┘        └──────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

---

## 시스템 구성

### 핵심 3개 서비스 구조

```
┌─────────────────────────────────────────────┐
│ 1. Backend API (Modular Monolith)           │
│    - 모든 비즈니스 로직을 모듈로 분리       │
│    - 단일 배포 단위                          │
│    - 필요시 모듈을 서비스로 분리 가능        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 2. Market Data Service (독립 서비스)        │
│    - 실시간 데이터 처리 특화                │
│    - WebSocket 서버                          │
│    - 고성능 요구사항으로 분리                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 3. Broker Connector (독립 서비스)           │
│    - 증권사 API 연동                         │
│    - API 변경 시 독립적 업데이트             │
│    - 장애 격리                               │
└─────────────────────────────────────────────┘
```

---

### 1. Backend API (Modular Monolith)

**역할**: 모든 핵심 비즈니스 로직 통합

#### 모듈 구조

```
backend/
├── src/
│   ├── auth/                  # 인증/인가
│   │   ├── auth.controller.ts
│   │   ├── auth.service.ts
│   │   ├── jwt.strategy.ts
│   │   └── dto/
│   │
│   ├── user/                  # 사용자 관리
│   │   ├── user.controller.ts
│   │   ├── user.service.ts
│   │   └── entities/user.entity.ts
│   │
│   ├── account/               # 계좌 관리
│   │   ├── account.controller.ts
│   │   ├── account.service.ts
│   │   └── entities/account.entity.ts
│   │
│   ├── trading/               # 주문 처리
│   │   ├── trading.controller.ts
│   │   ├── trading.service.ts
│   │   ├── order.engine.ts
│   │   └── entities/order.entity.ts
│   │
│   ├── portfolio/             # 포트폴리오
│   │   ├── portfolio.controller.ts
│   │   ├── portfolio.service.ts
│   │   └── entities/position.entity.ts
│   │
│   ├── risk/                  # 리스크 관리
│   │   ├── risk.service.ts
│   │   └── validators/
│   │
│   ├── analytics/             # 분석/통계
│   │   ├── analytics.controller.ts
│   │   ├── analytics.service.ts
│   │   └── backtest.engine.ts
│   │
│   ├── notification/          # 알림
│   │   ├── notification.service.ts
│   │   └── channels/
│   │
│   ├── common/                # 공통 모듈
│   │   ├── database/
│   │   ├── config/
│   │   ├── utils/
│   │   └── decorators/
│   │
│   └── main.ts
│
├── test/
├── package.json
└── tsconfig.json
```

#### API 엔드포인트 (통합)

```typescript
// 인증
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh

// 사용자
GET    /api/users/profile
PUT    /api/users/profile
POST   /api/users/2fa/enable

// 계좌
GET    /api/accounts
POST   /api/accounts
GET    /api/accounts/:id/balance
POST   /api/accounts/:id/deposit

// 주문
POST   /api/orders
GET    /api/orders
GET    /api/orders/:id
DELETE /api/orders/:id

// 포트폴리오
GET    /api/portfolio
GET    /api/portfolio/positions
GET    /api/portfolio/performance

// 분석
GET    /api/analytics/performance
POST   /api/analytics/backtest
GET    /api/analytics/reports/:id

// 시장 (프록시)
GET    /api/market/quote/:symbol
GET    /api/market/history/:symbol
```

---

### 2. Market Data Service

**역할**: 실시간 시세 데이터 전문 서비스

**기술 선택**: Go 또는 Python (asyncio)

#### 구조

```
market-data-service/
├── main.go (or main.py)
├── api/
│   ├── rest.go              # REST API
│   └── websocket.go         # WebSocket 서버
├── providers/
│   ├── yahoo_finance.go
│   ├── alpha_vantage.go
│   └── interface.go
├── cache/
│   └── redis.go
└── config/
    └── config.go
```

#### 기능

```yaml
data_ingestion:
  - 외부 API 폴링 (Yahoo Finance, Alpha Vantage)
  - 데이터 정규화
  - Redis 캐싱

websocket_server:
  - 클라이언트 연결 관리
  - 실시간 시세 브로드캐스트
  - 구독 관리

rest_api:
  - GET /quote/:symbol        # 현재가
  - GET /history/:symbol      # 과거 데이터
  - GET /orderbook/:symbol    # 호가 (가능시)
```

#### WebSocket 프로토콜

```json
// 구독
{
  "action": "subscribe",
  "symbols": ["AAPL", "TSLA", "005930.KS"]
}

// 시세 수신
{
  "type": "quote",
  "symbol": "AAPL",
  "price": 150.25,
  "change": 1.5,
  "changePercent": 1.01,
  "volume": 1000000,
  "timestamp": 1234567890
}
```

---

### 3. Broker Connector Service

**역할**: 증권사 API 통합 및 주문 전송

**기술 선택**: Python (증권사 SDK 대부분 Python)

#### 구조

```
broker-connector/
├── main.py
├── api/
│   └── routes.py
├── brokers/
│   ├── base.py               # 추상 인터페이스
│   ├── kiwoom.py             # 키움증권
│   ├── ebest.py              # 이베스트
│   ├── alpaca.py             # Alpaca (해외)
│   └── simulator.py          # 시뮬레이터
├── adapters/
│   └── order_adapter.py      # 주문 형식 변환
└── config/
    └── brokers.yaml
```

#### API

```python
# 연결
POST   /broker/connect
{
  "broker": "kiwoom",
  "api_key": "...",
  "api_secret": "..."
}

# 주문 전송
POST   /broker/order
{
  "symbol": "005930",
  "side": "buy",
  "quantity": 10,
  "price": 70000,
  "order_type": "limit"
}

# 계좌 동기화
GET    /broker/accounts/:account_id/sync

# 체결 내역
GET    /broker/executions
```

#### 브로커 추상화

```python
# broker/base.py
class BrokerInterface(ABC):
    @abstractmethod
    def connect(self, credentials: dict) -> bool:
        pass

    @abstractmethod
    def place_order(self, order: Order) -> OrderResult:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        pass

    @abstractmethod
    def get_balance(self) -> Balance:
        pass
```

---

## 기술 스택

### Backend API

#### 옵션 1: Python (FastAPI) - 추천 ⭐

```yaml
장점:
  - 빠른 개발 속도
  - 풍부한 데이터 분석 라이브러리
  - 증권사 SDK 대부분 Python
  - 비동기 처리 (asyncio)

스택:
  - FastAPI (웹 프레임워크)
  - SQLAlchemy (ORM)
  - Alembic (마이그레이션)
  - Pydantic (검증)
  - Celery (백그라운드 작업)
  - pytest (테스트)
```

#### 옵션 2: Node.js (NestJS)

```yaml
장점:
  - TypeScript 타입 안정성
  - 풍부한 생태계
  - WebSocket 성능 우수

스택:
  - NestJS (프레임워크)
  - TypeORM (ORM)
  - Passport (인증)
  - Jest (테스트)
```

### Market Data Service

**Go** (고성능 실시간 처리)
```yaml
라이브러리:
  - Gin (웹 프레임워크)
  - gorilla/websocket
  - go-redis
```

또는 **Python** (통합 관리 용이)
```yaml
라이브러리:
  - FastAPI
  - websockets
  - aioredis
  - yfinance
```

### Broker Connector

**Python** (필수)
```yaml
라이브러리:
  - PyKiwoom (키움)
  - python-xingAPI (이베스트)
  - mojito (한국투자증권)
  - alpaca-trade-api
```

### Frontend

**React + TypeScript**
```yaml
주요 라이브러리:
  - React 18
  - TanStack Query (서버 상태)
  - Zustand (클라이언트 상태)
  - React Router
  - Recharts (차트)
  - TailwindCSS (스타일)
  - Socket.io-client (실시간)
```

### 데이터베이스

**PostgreSQL 14+** (단일 DB)
```yaml
확장:
  - TimescaleDB (시계열 데이터 - 선택)

스키마:
  - public (기본)
  - trading (거래 관련)
  - analytics (분석 결과)
```

**Redis 7+** (캐싱/세션)
```yaml
용도:
  - 세션 저장
  - 실시간 시세 캐싱
  - Rate limiting
  - 작업 큐
```

---

## 데이터베이스 설계

### ERD (핵심 테이블만)

```sql
-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 계좌 (시뮬레이터/실전 구분)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    account_type VARCHAR(20) NOT NULL, -- 'simulator' | 'live'
    broker VARCHAR(50),                 -- 증권사명
    account_number VARCHAR(50),         -- 계좌번호
    balance DECIMAL(15, 2) DEFAULT 0,   -- 현금 잔고
    initial_balance DECIMAL(15, 2),     -- 초기 자금
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, account_type, broker)
);

-- 주문
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    symbol VARCHAR(20) NOT NULL,        -- 종목 코드
    side VARCHAR(10) NOT NULL,          -- 'buy' | 'sell'
    order_type VARCHAR(20) NOT NULL,    -- 'market' | 'limit' | 'stop'
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 2),
    status VARCHAR(20) NOT NULL,        -- 'pending' | 'filled' | 'cancelled'
    filled_quantity INTEGER DEFAULT 0,
    filled_price DECIMAL(12, 2),
    commission DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 체결 내역
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- 포지션 (보유 종목)
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES accounts(id),
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(12, 2) NOT NULL,  -- 평균 매입가
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(account_id, symbol)
);

-- 시장 데이터 (선택적 - 주로 Redis 사용)
CREATE TABLE market_prices (
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    volume BIGINT,
    timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);

-- TimescaleDB 활성화 시
-- SELECT create_hypertable('market_prices', 'timestamp');

-- 알림 설정
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(20) NOT NULL,    -- 'price_above' | 'price_below'
    target_price DECIMAL(12, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 리스크 한도 설정
CREATE TABLE risk_limits (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    max_daily_loss DECIMAL(15, 2),
    max_position_size DECIMAL(5, 2),    -- 최대 비중 (%)
    max_order_value DECIMAL(15, 2),
    max_leverage DECIMAL(5, 2) DEFAULT 1.0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_positions_account_id ON positions(account_id);
CREATE INDEX idx_executions_order_id ON executions(order_id);
CREATE INDEX idx_market_prices_symbol ON market_prices(symbol);
```

---

## 배포 전략

### 개발 환경: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: trading
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  # Backend API
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD}@postgres:5432/trading
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Market Data Service
  market-data:
    build: ./market-data-service
    ports:
      - "8001:8001"
    environment:
      REDIS_URL: redis://redis:6379
      ALPHA_VANTAGE_KEY: ${ALPHA_VANTAGE_KEY}
    depends_on:
      - redis

  # Broker Connector
  broker-connector:
    build: ./broker-connector
    ports:
      - "8002:8002"
    environment:
      DATABASE_URL: postgresql://admin:${DB_PASSWORD}@postgres:5432/trading
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./broker-connector:/app

  # Frontend
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_WS_URL: ws://localhost:8001
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm start

volumes:
  postgres_data:
  redis_data:
```

### 실행 명령어

```bash
# 개발 환경 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 서비스 재시작
docker-compose restart backend

# 중지
docker-compose down

# DB 초기화 포함 중지
docker-compose down -v
```

---

### 프로덕션: 저렴한 VPS 배포

#### 옵션 1: 단일 VPS (가장 저렴)

**추천 사양**:
```yaml
provider: DigitalOcean / Vultr / Hetzner
spec:
  - CPU: 2 vCPU
  - RAM: 4GB
  - Storage: 80GB SSD
  - 비용: $12-24/월

설치:
  - Docker
  - Docker Compose
  - Nginx (리버스 프록시)
  - Let's Encrypt (SSL)
```

**배포 스크립트**:
```bash
#!/bin/bash
# deploy.sh

# 1. 코드 풀
git pull origin main

# 2. 환경 변수 로드
source .env.production

# 3. 빌드 및 재시작
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. 헬스 체크
curl http://localhost:8000/health

# 5. Nginx 리로드
sudo nginx -s reload
```

**Nginx 설정**:
```nginx
# /etc/nginx/sites-available/trading

upstream backend {
    server localhost:8000;
}

upstream websocket {
    server localhost:8001;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/trading/frontend/build;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

#### 옵션 2: 관리형 서비스 (편의성 우선)

```yaml
backend:
  - Heroku / Railway / Render
  - 비용: $7-15/월

database:
  - Supabase (PostgreSQL)
  - 비용: 무료 (500MB) ~ $25/월

redis:
  - Upstash
  - 비용: 무료 (10K requests) ~ $10/월

frontend:
  - Vercel / Netlify
  - 비용: 무료
```

**장점**: 관리 부담 최소화
**단점**: 비용 약간 높음 (~$50/월)

---

#### 옵션 3: 홈 서버 (최저 비용)

```yaml
hardware:
  - Raspberry Pi 4 (8GB)
  - 또는 중고 미니 PC

비용:
  - 하드웨어: $100-200 (1회)
  - 전기세: ~$5/월
  - 도메인: $10/년

주의사항:
  - 고정 IP 또는 DDNS 필요
  - UPS 권장 (정전 대비)
  - 24시간 가동
```

---

## 개발 로드맵

### Phase 1: MVP 개발 (4주)

#### Week 1: 기반 구조
```yaml
tasks:
  - [x] 프로젝트 구조 생성
  - [x] Docker Compose 환경 설정
  - [x] PostgreSQL 스키마 설계
  - [x] Backend API 스켈레톤
  - [x] Frontend 프로젝트 초기화

deliverables:
  - 로컬 개발 환경
  - 데이터베이스 마이그레이션
  - Hello World API
```

#### Week 2: 인증 & 계좌
```yaml
tasks:
  - [x] 사용자 등록/로그인
  - [x] JWT 인증
  - [x] 계좌 생성 (시뮬레이터)
  - [x] 잔고 조회

deliverables:
  - 인증 API
  - 계좌 관리 API
  - 기본 Frontend (로그인/회원가입)
```

#### Week 3: 거래 기능
```yaml
tasks:
  - [x] 주문 생성/취소
  - [x] 시뮬레이터 주문 체결 로직
  - [x] 포지션 관리
  - [x] 거래 내역 조회

deliverables:
  - 주문 API
  - 포트폴리오 API
  - 주문 화면 (Frontend)
```

#### Week 4: 시장 데이터
```yaml
tasks:
  - [x] Market Data Service 개발
  - [x] Yahoo Finance API 연동
  - [x] WebSocket 서버
  - [x] 실시간 차트 컴포넌트

deliverables:
  - 시세 조회 API
  - 실시간 WebSocket
  - 차트 페이지
```

**MVP 완료**: 시뮬레이터로 주식 거래 가능

---

### Phase 2: 실전 거래 연동 (3주)

#### Week 5-6: Broker Connector
```yaml
tasks:
  - [x] Broker Connector Service 개발
  - [x] 키움증권 API 연동
  - [x] 주문 라우팅 로직
  - [x] 계좌 동기화

deliverables:
  - 증권사 연결 API
  - 실전 주문 기능
```

#### Week 7: 리스크 관리
```yaml
tasks:
  - [x] 리스크 검증 로직
  - [x] 한도 설정 UI
  - [x] 주문 확인 모달
  - [x] 경고 알림

deliverables:
  - 리스크 관리 시스템
  - 안전장치
```

---

### Phase 3: 고급 기능 (3주)

#### Week 8: 분석 도구
```yaml
tasks:
  - [x] 포트폴리오 성과 분석
  - [x] 수익률 계산
  - [x] 차트 고도화
  - [x] 거래 통계

deliverables:
  - Analytics API
  - 대시보드 페이지
```

#### Week 9: 백테스팅
```yaml
tasks:
  - [x] 백테스트 엔진
  - [x] 과거 데이터 로드
  - [x] 전략 실행
  - [x] 결과 시각화

deliverables:
  - 백테스트 API
  - 전략 테스트 페이지
```

#### Week 10: 알림 & 개선
```yaml
tasks:
  - [x] 이메일 알림
  - [x] 가격 알림
  - [x] UI/UX 개선
  - [x] 버그 수정

deliverables:
  - 알림 시스템
  - 안정화
```

---

### 전체 타임라인

```
Week 1-4:   Phase 1 (MVP - 시뮬레이터)
Week 5-7:   Phase 2 (실전 거래)
Week 8-10:  Phase 3 (고급 기능)

Total: 10주 (2.5개월)
```

---

## 비용 분석

### 개발 비용

```yaml
시간 투자:
  - 주당 20시간 작업
  - 10주 = 200시간

학습 곡선:
  - FastAPI/NestJS: 1주
  - React: 1주
  - 증권사 API: 2주
```

### 운영 비용 (월간)

#### 옵션 A: VPS (추천)
```yaml
VPS (4GB RAM): $20
도메인: $1
SSL: 무료 (Let's Encrypt)
백업 스토리지: $5

Total: ~$26/월
```

#### 옵션 B: 관리형 서비스
```yaml
Backend (Railway): $10
Database (Supabase): $25
Redis (Upstash): $10
Frontend (Vercel): 무료

Total: ~$45/월
```

#### 옵션 C: 홈 서버
```yaml
전기세: $5
도메인: $1
DDNS (선택): $2

Total: ~$8/월
```

### 외부 API 비용

```yaml
무료 티어 활용:
  - Yahoo Finance: 무료
  - Alpha Vantage: 무료 (500 req/day)
  - 증권사 API: 무료 (계좌 보유 시)

유료 전환 시:
  - Alpha Vantage Premium: $50/월
  - IEX Cloud: $9/월
```

---

## 보안 체크리스트

```yaml
필수 보안 조치:
  - [x] 환경 변수로 비밀 관리 (.env)
  - [x] JWT Secret 강력한 키 사용
  - [x] HTTPS 적용 (SSL 인증서)
  - [x] API Rate Limiting
  - [x] SQL Injection 방지 (ORM 사용)
  - [x] XSS 방지 (입력 검증)
  - [x] CORS 설정
  - [x] 비밀번호 해싱 (bcrypt)
  - [x] 2FA 구현
  - [x] API Key 암호화 저장

권장 보안 조치:
  - [ ] VPN 또는 IP 화이트리스트
  - [ ] 침입 탐지 (Fail2ban)
  - [ ] 정기 백업 (일 1회)
  - [ ] 로그 모니터링
  - [ ] 보안 업데이트 자동화
```

---

## 모니터링 & 로깅

### 최소 모니터링 (무료)

```yaml
애플리케이션 로그:
  - Python: logging 모듈
  - Node.js: Winston
  - 출력: stdout → Docker logs

헬스 체크:
  - GET /health 엔드포인트
  - Uptime 모니터링: UptimeRobot (무료)

에러 추적:
  - Sentry (무료 티어)
```

### 간단한 로그 설정

```python
# backend/config/logging.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger("trading")
    logger.setLevel(logging.INFO)

    # 파일 핸들러 (10MB, 5개 파일 로테이션)
    handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

---

## 백업 전략

### 데이터베이스 백업

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL 백업
docker exec postgres pg_dump -U admin trading > \
    "$BACKUP_DIR/trading_$DATE.sql"

# 압축
gzip "$BACKUP_DIR/trading_$DATE.sql"

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

# 클라우드 업로드 (선택)
# rclone copy "$BACKUP_DIR/trading_$DATE.sql.gz" remote:backups/
```

### Cron 설정

```bash
# 매일 새벽 2시 백업
0 2 * * * /home/user/backup.sh
```

---

## 개발 팁

### 효율적인 개발 흐름

```yaml
단계별 접근:
  1. Backend API 먼저 개발 (Swagger 문서화)
  2. Postman/Thunder Client로 테스트
  3. Frontend는 완성된 API 사용
  4. 통합 테스트

재사용 가능한 코드:
  - 공통 유틸리티 함수
  - API 클라이언트 래퍼
  - 커스텀 React Hooks

테스트 전략:
  - 단위 테스트: 비즈니스 로직만
  - 통합 테스트: 주문 플로우
  - E2E 테스트: 생략 가능 (개인 프로젝트)
```

### 추천 개발 도구

```yaml
IDE:
  - VS Code + 확장
    - Python
    - ESLint
    - Prettier
    - Docker

API 테스트:
  - Thunder Client (VS Code 확장)
  - Postman

데이터베이스:
  - DBeaver (GUI)
  - TablePlus

버전 관리:
  - Git + GitHub
```

---

## 확장 가능성

### 나중에 추가할 수 있는 기능

```yaml
phase_4_features:
  - 다중 사용자 지원 (친구 초대)
  - 소셜 기능 (거래 공유)
  - 모바일 앱 (React Native)
  - 알고리즘 트레이딩
  - 옵션/선물 거래
  - 암호화폐 거래

확장 전략:
  - 모듈 단위로 개발했으므로
  - 필요한 모듈을 독립 서비스로 분리 가능
  - 점진적 확장 (Strangler Pattern)
```

---

## 다음 단계

### 즉시 시작하기

```bash
# 1. 프로젝트 디렉토리 생성
mkdir personal-trading-system
cd personal-trading-system

# 2. 하위 디렉토리 생성
mkdir -p backend frontend market-data-service broker-connector

# 3. Docker Compose 파일 생성
touch docker-compose.yml

# 4. 환경 변수 파일 생성
touch .env
echo "DB_PASSWORD=your_secure_password" >> .env
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env

# 5. Git 초기화
git init
touch .gitignore
echo ".env" >> .gitignore
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### 학습 자료

```yaml
Backend (FastAPI):
  - 공식 문서: https://fastapi.tiangolo.com/
  - Tutorial: FastAPI 입문 가이드

Frontend (React):
  - React 공식 문서
  - TanStack Query 문서

증권사 API:
  - PyKiwoom GitHub
  - 키움증권 OpenAPI 가이드

DevOps:
  - Docker Compose 문서
  - Nginx 설정 가이드
```

---

## 요약

### 왜 이 아키텍처가 개인용에 적합한가?

```yaml
단순성:
  - 3개 서비스만 관리
  - 단일 데이터베이스
  - Docker Compose로 쉬운 배포

유지보수성:
  - 모듈화된 구조
  - 명확한 책임 분리
  - 표준 기술 스택

비용 효율성:
  - VPS: ~$20/월
  - 무료 API 활용
  - 홈 서버 옵션

확장성:
  - 모듈을 서비스로 분리 가능
  - 점진적 확장
```

### 핵심 차이점 (vs 엔터프라이즈)

| 항목 | 엔터프라이즈 | 개인용 |
|------|------------|--------|
| 서비스 수 | 11개 | 3개 |
| 데이터베이스 | 서비스별 분리 | 단일 DB |
| 메시지 큐 | Kafka + RabbitMQ | 선택적 |
| 모니터링 | Prometheus + Grafana | 기본 로깅 |
| 배포 | Kubernetes | Docker Compose |
| 비용 | $2,000/월 | $20/월 |
| 개발 기간 | 30주 | 10주 |

---

**문서 버전**: 1.0 (개인용)
**작성일**: 2026-02-07
**다음 단계**: Phase 1 구현 시작
