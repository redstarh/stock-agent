# TDD (Test-Driven Development) 가이드

> **프로젝트**: Personal Trading System
> **테스트 전략**: Unit → Integration → E2E
> **목표**: 80% 이상 테스트 커버리지

---

## 📋 목차

1. [TDD 개요](#tdd-개요)
2. [테스트 피라미드](#테스트-피라미드)
3. [테스트 레벨별 전략](#테스트-레벨별-전략)
4. [기술 스택 & 도구](#기술-스택--도구)
5. [TDD 워크플로우](#tdd-워크플로우)
6. [Backend 테스트](#backend-테스트)
7. [Frontend 테스트](#frontend-테스트)
8. [E2E 테스트](#e2e-테스트)
9. [CI/CD 통합](#cicd-통합)
10. [실전 예제](#실전-예제)

---

## TDD 개요

### TDD란?

**Test-Driven Development**: 테스트를 먼저 작성하고, 그 테스트를 통과하는 최소한의 코드를 작성하는 개발 방법론

### Red-Green-Refactor 사이클

```mermaid
graph LR
    A[🔴 Red: 실패하는 테스트 작성] --> B[🟢 Green: 테스트 통과하는 코드 작성]
    B --> C[🔵 Refactor: 코드 개선]
    C --> A

    style A fill:#ffcdd2
    style B fill:#c8e6c9
    style C fill:#bbdefb
```

#### 1️⃣ Red (실패)
```python
# 테스트 먼저 작성 (아직 구현 안됨)
def test_create_order():
    order = create_order(symbol="AAPL", quantity=10, price=150.0)
    assert order.symbol == "AAPL"
    assert order.status == "PENDING"
```

#### 2️⃣ Green (성공)
```python
# 테스트를 통과하는 최소한의 코드
def create_order(symbol, quantity, price):
    return Order(symbol=symbol, quantity=quantity, price=price, status="PENDING")
```

#### 3️⃣ Refactor (개선)
```python
# 코드 개선 (테스트는 그대로 유지)
def create_order(symbol: str, quantity: int, price: Decimal) -> Order:
    """주문 생성"""
    validate_symbol(symbol)
    validate_quantity(quantity)

    return Order(
        symbol=symbol,
        quantity=quantity,
        price=price,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
```

---

### TDD의 장점

```yaml
코드 품질:
  - ✅ 버그 조기 발견
  - ✅ 명확한 요구사항 정의
  - ✅ 리팩토링 안전성

개발 속도:
  - ✅ 디버깅 시간 감소
  - ✅ 회귀 테스트 자동화
  - ✅ 문서화 역할

설계 개선:
  - ✅ 모듈화된 코드
  - ✅ 의존성 분리
  - ✅ SOLID 원칙 자연스럽게 적용
```

---

## 테스트 피라미드

```
        ╱╲
       ╱  ╲
      ╱ E2E╲     10%  (느림, 비용 높음)
     ╱──────╲
    ╱        ╲
   ╱Integration╲  20%  (중간)
  ╱────────────╲
 ╱              ╲
╱  Unit Tests   ╲ 70%  (빠름, 비용 낮음)
╲────────────────╱
```

### 비율 가이드

| 테스트 유형 | 비율 | 개수 (예상) | 실행 시간 | 비용 |
|------------|------|------------|----------|------|
| **Unit Tests** | 70% | ~200개 | < 10초 | 낮음 |
| **Integration Tests** | 20% | ~50개 | 30-60초 | 중간 |
| **E2E Tests** | 10% | ~20개 | 2-5분 | 높음 |

---

## 테스트 레벨별 전략

### 1. Unit Tests (단위 테스트)

**목적**: 개별 함수/메서드의 정확성 검증

**대상**:
- 비즈니스 로직 (계산, 검증)
- 유틸리티 함수
- 모델 메서드

**예시**:
```python
# 포트폴리오 수익률 계산
def test_calculate_roi():
    portfolio = Portfolio(initial_balance=10000)
    portfolio.add_position("AAPL", quantity=10, price=100)

    roi = portfolio.calculate_roi(current_price=120)
    assert roi == 20.0  # 20% 수익
```

**특징**:
- ✅ 빠른 실행 (< 1초)
- ✅ 외부 의존성 없음 (Mock 사용)
- ✅ 높은 커버리지 가능

---

### 2. Integration Tests (통합 테스트)

**목적**: 컴포넌트 간 상호작용 검증

**대상**:
- API 엔드포인트
- 데이터베이스 연동
- 외부 서비스 호출

**예시**:
```python
# 주문 API 테스트
def test_create_order_api(client, db_session):
    response = client.post("/api/orders", json={
        "symbol": "AAPL",
        "quantity": 10,
        "price": 150.0,
        "side": "buy"
    })

    assert response.status_code == 201
    order = db_session.query(Order).first()
    assert order.symbol == "AAPL"
```

**특징**:
- ✅ 실제 DB 사용 (테스트 DB)
- ✅ API 계약 검증
- ⚠️ 중간 속도 (1-5초)

---

### 3. Component Tests (컴포넌트 테스트)

**목적**: UI 컴포넌트 동작 검증

**대상**:
- React 컴포넌트
- 사용자 인터랙션
- 상태 관리

**예시**:
```javascript
// 주문 폼 컴포넌트 테스트
test('should submit order when form is valid', async () => {
  render(<OrderForm />);

  fireEvent.change(screen.getByLabelText('Symbol'), { target: { value: 'AAPL' } });
  fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '10' } });
  fireEvent.click(screen.getByText('Buy'));

  await waitFor(() => {
    expect(screen.getByText('Order submitted')).toBeInTheDocument();
  });
});
```

**특징**:
- ✅ 사용자 관점 테스트
- ✅ 렌더링 검증
- ⚠️ DOM 조작 필요

---

### 4. Contract Tests (계약 테스트)

**목적**: API 계약 준수 검증

**대상**:
- Backend API 스펙
- Frontend API 클라이언트
- 서비스 간 인터페이스

**예시**:
```python
# Pact를 사용한 Contract Test
def test_get_order_contract(pact):
    pact.given('An order exists').upon_receiving(
        'a request for order details'
    ).with_request(
        'GET', '/api/orders/123'
    ).will_respond_with(200, body={
        'id': '123',
        'symbol': 'AAPL',
        'status': 'PENDING'
    })

    # Frontend가 이 계약을 준수하는지 검증
```

**특징**:
- ✅ API 변경 감지
- ✅ Frontend/Backend 독립 개발
- ✅ 문서화 역할

---

### 5. E2E Tests (End-to-End 테스트)

**목적**: 전체 사용자 플로우 검증

**대상**:
- 주요 비즈니스 시나리오
- 크리티컬 패스
- 사용자 여정

**예시**:
```javascript
// Playwright E2E 테스트
test('complete trading flow', async ({ page }) => {
  // 로그인
  await page.goto('https://localhost:3000');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  // 주문 생성
  await page.click('text=New Order');
  await page.fill('[name="symbol"]', 'AAPL');
  await page.fill('[name="quantity"]', '10');
  await page.click('text=Buy');

  // 포트폴리오 확인
  await page.click('text=Portfolio');
  await expect(page.locator('text=AAPL')).toBeVisible();
});
```

**특징**:
- ✅ 실제 사용자 시나리오
- ✅ 전체 스택 검증
- ⚠️ 느림 (10초 ~ 1분)
- ⚠️ 깨지기 쉬움 (Flaky)

---

## 기술 스택 & 도구

### Backend (Python/FastAPI)

```yaml
프레임워크:
  - pytest: 테스트 러너
  - pytest-asyncio: 비동기 테스트
  - pytest-cov: 커버리지 측정

Mocking:
  - pytest-mock: Mock 객체
  - faker: 더미 데이터 생성
  - freezegun: 시간 고정

DB 테스트:
  - pytest-postgresql: PostgreSQL fixture
  - factory-boy: 테스트 데이터 팩토리

API 테스트:
  - httpx: HTTP 클라이언트
  - TestClient (FastAPI): API 테스트
```

### Frontend (React/TypeScript)

```yaml
프레임워크:
  - Jest: 테스트 러너
  - React Testing Library: 컴포넌트 테스트
  - @testing-library/user-event: 사용자 이벤트

Mocking:
  - MSW (Mock Service Worker): API 모킹
  - jest-mock: Mock 함수

E2E:
  - Playwright: 브라우저 자동화
  - Cypress: (대안)
```

### 통합 테스트

```yaml
Contract Testing:
  - Pact: Consumer-Driven Contracts

Performance:
  - Locust: 부하 테스트
  - K6: 성능 테스트
```

---

## TDD 워크플로우

### 개발 프로세스

```mermaid
graph TD
    A[요구사항 분석] --> B[테스트 케이스 작성]
    B --> C[테스트 실행 - FAIL]
    C --> D[최소 코드 작성]
    D --> E[테스트 실행 - PASS]
    E --> F{리팩토링 필요?}
    F -->|Yes| G[코드 개선]
    G --> E
    F -->|No| H[다음 기능]
    H --> B

    style C fill:#ffcdd2
    style E fill:#c8e6c9
    style G fill:#bbdefb
```

### 일일 개발 루틴

```bash
# 1. 새 기능 시작
git checkout -b feature/portfolio-api

# 2. 테스트 작성
# tests/test_portfolio.py

# 3. 테스트 실행 (실패 확인)
pytest tests/test_portfolio.py -v

# 4. 코드 작성
# src/portfolio/service.py

# 5. 테스트 실행 (성공 확인)
pytest tests/test_portfolio.py -v

# 6. 커버리지 확인
pytest --cov=src --cov-report=html

# 7. 리팩토링
# 코드 개선

# 8. 모든 테스트 실행
pytest

# 9. 커밋
git add .
git commit -m "feat: add portfolio calculation"
```

---

## Backend 테스트

### 프로젝트 구조

```
backend/
├── src/
│   ├── auth/
│   ├── trading/
│   ├── portfolio/
│   └── common/
├── tests/
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_trading.py
│   │   └── test_portfolio.py
│   ├── integration/
│   │   ├── test_api_auth.py
│   │   ├── test_api_trading.py
│   │   └── test_api_portfolio.py
│   └── conftest.py
├── pytest.ini
└── requirements-dev.txt
```

### pytest.ini 설정

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 테스트 옵션
addopts =
    -v
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

# 마커 정의
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    auth: Authentication tests
    trading: Trading tests
    portfolio: Portfolio tests
```

### conftest.py (테스트 픽스처)

```python
"""
공통 테스트 픽스처
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from src.main import app
from src.database import Base, get_db
from src.auth.models import User
from src.trading.models import Order, Position


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def db_engine():
    """테스트용 DB 엔진"""
    engine = create_engine(
        "postgresql://test:test@localhost:5432/test_trading",
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """테스트용 DB 세션"""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI 테스트 클라이언트"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ==================== User Fixtures ====================

@pytest.fixture
def test_user(db_session):
    """테스트 사용자"""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$...",  # bcrypt hash
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """인증 헤더"""
    token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}


# ==================== Trading Fixtures ====================

@pytest.fixture
def test_account(db_session, test_user):
    """테스트 계좌"""
    account = Account(
        user_id=test_user.id,
        account_type="simulator",
        balance=10000.0
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def test_order(db_session, test_account):
    """테스트 주문"""
    order = Order(
        account_id=test_account.id,
        symbol="AAPL",
        side="buy",
        quantity=10,
        price=150.0,
        status="pending"
    )
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def test_position(db_session, test_account):
    """테스트 포지션"""
    position = Position(
        account_id=test_account.id,
        symbol="AAPL",
        quantity=10,
        avg_price=150.0
    )
    db_session.add(position)
    db_session.commit()
    return position
```

---

### Unit Tests 예제

#### 1. 모델 테스트

```python
# tests/unit/test_order_model.py
"""
Order 모델 단위 테스트
"""
import pytest
from decimal import Decimal
from src.trading.models import Order, OrderStatus


class TestOrderModel:
    """Order 모델 테스트"""

    def test_create_order(self):
        """주문 생성 테스트"""
        order = Order(
            account_id=1,
            symbol="AAPL",
            side="buy",
            quantity=10,
            price=Decimal("150.00"),
            status=OrderStatus.PENDING
        )

        assert order.symbol == "AAPL"
        assert order.quantity == 10
        assert order.total_value == Decimal("1500.00")

    def test_order_status_transition(self):
        """주문 상태 전환 테스트"""
        order = Order(symbol="AAPL", quantity=10, price=150.0)

        # PENDING → FILLED
        order.mark_as_filled(filled_price=151.0)
        assert order.status == OrderStatus.FILLED
        assert order.filled_price == 151.0

        # FILLED → CANCELLED (불가능)
        with pytest.raises(ValueError):
            order.cancel()

    def test_calculate_commission(self):
        """수수료 계산 테스트"""
        order = Order(symbol="AAPL", quantity=100, price=150.0)

        # 0.1% 수수료
        commission = order.calculate_commission(rate=0.001)
        assert commission == Decimal("15.00")
```

#### 2. 서비스 로직 테스트

```python
# tests/unit/test_portfolio_service.py
"""
Portfolio 서비스 단위 테스트
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.portfolio.service import PortfolioService
from src.portfolio.models import Position


class TestPortfolioService:
    """포트폴리오 서비스 테스트"""

    @pytest.fixture
    def portfolio_service(self):
        return PortfolioService()

    def test_calculate_position_value(self, portfolio_service):
        """포지션 평가액 계산"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            avg_price=Decimal("150.00")
        )

        current_price = Decimal("160.00")
        value = portfolio_service.calculate_position_value(
            position, current_price
        )

        assert value == Decimal("1600.00")

    def test_calculate_unrealized_pnl(self, portfolio_service):
        """미실현 손익 계산"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            avg_price=Decimal("150.00")
        )

        current_price = Decimal("160.00")
        pnl = portfolio_service.calculate_unrealized_pnl(
            position, current_price
        )

        assert pnl == Decimal("100.00")  # (160 - 150) * 10

    def test_calculate_roi(self, portfolio_service):
        """ROI 계산"""
        position = Position(
            symbol="AAPL",
            quantity=10,
            avg_price=Decimal("150.00")
        )

        current_price = Decimal("165.00")
        roi = portfolio_service.calculate_roi(position, current_price)

        assert roi == Decimal("10.00")  # (165 - 150) / 150 * 100

    @patch('src.market_data.service.MarketDataService.get_current_price')
    def test_get_portfolio_value_with_mock(
        self, mock_get_price, portfolio_service
    ):
        """Mock을 사용한 포트폴리오 평가액 계산"""
        # Mock 설정
        mock_get_price.return_value = Decimal("160.00")

        positions = [
            Position(symbol="AAPL", quantity=10, avg_price=150.0),
            Position(symbol="TSLA", quantity=5, avg_price=200.0)
        ]

        total_value = portfolio_service.get_portfolio_value(positions)

        # AAPL: 160 * 10 = 1600
        # TSLA: 160 * 5 = 800 (Mock은 모든 심볼에 대해 160 반환)
        assert total_value == Decimal("2400.00")
        assert mock_get_price.call_count == 2
```

#### 3. 비즈니스 로직 테스트 (리스크 관리)

```python
# tests/unit/test_risk_validator.py
"""
리스크 검증 단위 테스트
"""
import pytest
from decimal import Decimal

from src.risk.validator import RiskValidator, RiskViolation
from src.risk.models import RiskLimit


class TestRiskValidator:
    """리스크 검증 테스트"""

    @pytest.fixture
    def risk_limit(self):
        return RiskLimit(
            max_daily_loss=Decimal("1000.00"),
            max_position_size=Decimal("30.00"),  # 30%
            max_order_value=Decimal("5000.00")
        )

    @pytest.fixture
    def validator(self, risk_limit):
        return RiskValidator(risk_limit)

    def test_validate_order_within_limit(self, validator):
        """한도 내 주문 검증"""
        order_value = Decimal("3000.00")

        # 예외 발생하지 않아야 함
        validator.validate_order_value(order_value)

    def test_validate_order_exceeds_limit(self, validator):
        """한도 초과 주문 검증"""
        order_value = Decimal("6000.00")

        with pytest.raises(RiskViolation) as exc_info:
            validator.validate_order_value(order_value)

        assert "최대 주문 금액 초과" in str(exc_info.value)

    def test_validate_daily_loss(self, validator):
        """일일 손실 한도 검증"""
        current_loss = Decimal("500.00")
        new_loss = Decimal("600.00")

        # 합계 1100 > 1000 한도
        with pytest.raises(RiskViolation):
            validator.validate_daily_loss(current_loss, new_loss)

    def test_validate_position_size(self, validator):
        """포지션 크기 검증"""
        position_value = Decimal("4000.00")
        portfolio_value = Decimal("10000.00")

        # 40% > 30% 한도
        with pytest.raises(RiskViolation) as exc_info:
            validator.validate_position_size(
                position_value, portfolio_value
            )

        assert "최대 포지션 비중 초과" in str(exc_info.value)

    @pytest.mark.parametrize("current_loss,new_order_loss,expected", [
        (Decimal("0"), Decimal("500"), True),      # OK
        (Decimal("500"), Decimal("400"), True),    # OK (900 < 1000)
        (Decimal("800"), Decimal("300"), False),   # NG (1100 > 1000)
        (Decimal("1000"), Decimal("1"), False),    # NG (이미 한도)
    ])
    def test_validate_daily_loss_parametrized(
        self, validator, current_loss, new_order_loss, expected
    ):
        """파라미터화된 일일 손실 검증"""
        if expected:
            validator.validate_daily_loss(current_loss, new_order_loss)
        else:
            with pytest.raises(RiskViolation):
                validator.validate_daily_loss(current_loss, new_order_loss)
```

---

### Integration Tests 예제

#### 1. API 엔드포인트 테스트

```python
# tests/integration/test_api_orders.py
"""
주문 API 통합 테스트
"""
import pytest
from decimal import Decimal


class TestOrderAPI:
    """주문 API 테스트"""

    def test_create_order_success(
        self, client, test_account, auth_headers
    ):
        """주문 생성 성공"""
        response = client.post(
            "/api/orders",
            headers=auth_headers,
            json={
                "account_id": test_account.id,
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 10,
                "price": 150.0,
                "order_type": "limit"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_order_insufficient_balance(
        self, client, test_account, auth_headers
    ):
        """잔고 부족 주문 생성"""
        # 계좌 잔고: 10,000
        # 주문 금액: 100 * 200 = 20,000

        response = client.post(
            "/api/orders",
            headers=auth_headers,
            json={
                "account_id": test_account.id,
                "symbol": "TSLA",
                "side": "buy",
                "quantity": 100,
                "price": 200.0,
                "order_type": "limit"
            }
        )

        assert response.status_code == 400
        assert "잔고 부족" in response.json()["detail"]

    def test_get_orders(self, client, test_order, auth_headers):
        """주문 목록 조회"""
        response = client.get(
            "/api/orders",
            headers=auth_headers
        )

        assert response.status_code == 200
        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["symbol"] == "AAPL"

    def test_cancel_order(self, client, test_order, auth_headers):
        """주문 취소"""
        response = client.delete(
            f"/api/orders/{test_order.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_filled_order(
        self, client, db_session, test_order, auth_headers
    ):
        """체결된 주문 취소 시도 (실패)"""
        # 주문을 체결 상태로 변경
        test_order.status = "filled"
        db_session.commit()

        response = client.delete(
            f"/api/orders/{test_order.id}",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "체결된 주문" in response.json()["detail"]
```

#### 2. 트랜잭션 테스트

```python
# tests/integration/test_order_execution.py
"""
주문 실행 트랜잭션 테스트
"""
import pytest
from decimal import Decimal

from src.trading.service import TradingService


class TestOrderExecution:
    """주문 실행 통합 테스트"""

    @pytest.fixture
    def trading_service(self, db_session):
        return TradingService(db_session)

    def test_execute_buy_order_updates_balance_and_position(
        self, trading_service, test_account, db_session
    ):
        """매수 주문 실행 시 잔고와 포지션 업데이트"""
        initial_balance = test_account.balance

        # 매수 주문 실행
        order = trading_service.execute_order(
            account_id=test_account.id,
            symbol="AAPL",
            side="buy",
            quantity=10,
            price=Decimal("150.00")
        )

        # 주문 확인
        assert order.status == "filled"

        # 잔고 확인 (10 * 150 = 1500 차감)
        db_session.refresh(test_account)
        assert test_account.balance == initial_balance - Decimal("1500.00")

        # 포지션 확인
        position = db_session.query(Position).filter_by(
            account_id=test_account.id,
            symbol="AAPL"
        ).first()

        assert position is not None
        assert position.quantity == 10
        assert position.avg_price == Decimal("150.00")

    def test_execute_sell_order_updates_balance_and_position(
        self, trading_service, test_account, test_position, db_session
    ):
        """매도 주문 실행 시 잔고와 포지션 업데이트"""
        initial_balance = test_account.balance

        # 매도 주문 실행 (10주 중 5주 매도)
        order = trading_service.execute_order(
            account_id=test_account.id,
            symbol="AAPL",
            side="sell",
            quantity=5,
            price=Decimal("160.00")
        )

        # 주문 확인
        assert order.status == "filled"

        # 잔고 확인 (5 * 160 = 800 증가)
        db_session.refresh(test_account)
        assert test_account.balance == initial_balance + Decimal("800.00")

        # 포지션 확인 (10 - 5 = 5주 남음)
        db_session.refresh(test_position)
        assert test_position.quantity == 5

    def test_rollback_on_error(
        self, trading_service, test_account, db_session
    ):
        """에러 발생 시 트랜잭션 롤백"""
        initial_balance = test_account.balance

        # 잔고 부족 주문 시도
        with pytest.raises(InsufficientBalanceError):
            trading_service.execute_order(
                account_id=test_account.id,
                symbol="TSLA",
                side="buy",
                quantity=100,
                price=Decimal("200.00")
            )

        # 잔고 변경 없음 (롤백)
        db_session.refresh(test_account)
        assert test_account.balance == initial_balance

        # 주문 생성 안됨
        order_count = db_session.query(Order).count()
        assert order_count == 0
```

---

## Frontend 테스트

### 프로젝트 구조

```
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
├── __tests__/
│   ├── unit/
│   │   ├── utils.test.ts
│   │   └── hooks.test.tsx
│   ├── components/
│   │   ├── OrderForm.test.tsx
│   │   └── Portfolio.test.tsx
│   └── integration/
│       └── OrderFlow.test.tsx
├── e2e/
│   └── trading.spec.ts
└── jest.config.js
```

### jest.config.js

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',

  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },

  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
  ],

  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 80,
      statements: 80,
    },
  },
};
```

### jest.setup.js

```javascript
import '@testing-library/jest-dom';
import { server } from './src/mocks/server';

// MSW 서버 설정
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

### Component Tests 예제

#### 1. 단순 컴포넌트 테스트

```typescript
// __tests__/components/OrderButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { OrderButton } from '@/components/OrderButton';

describe('OrderButton', () => {
  it('renders buy button', () => {
    render(<OrderButton side="buy" onClick={jest.fn()} />);

    const button = screen.getByRole('button', { name: /buy/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('bg-green-500');
  });

  it('renders sell button', () => {
    render(<OrderButton side="sell" onClick={jest.fn()} />);

    const button = screen.getByRole('button', { name: /sell/i });
    expect(button).toHaveClass('bg-red-500');
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<OrderButton side="buy" onClick={handleClick} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when disabled prop is true', () => {
    render(<OrderButton side="buy" onClick={jest.fn()} disabled />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });
});
```

#### 2. 폼 컴포넌트 테스트

```typescript
// __tests__/components/OrderForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OrderForm } from '@/components/OrderForm';

describe('OrderForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<OrderForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/symbol/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/quantity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/price/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<OrderForm onSubmit={mockOnSubmit} />);

    // Submit without filling
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/symbol is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<OrderForm onSubmit={mockOnSubmit} />);

    // Fill form
    await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
    await user.type(screen.getByLabelText(/quantity/i), '10');
    await user.type(screen.getByLabelText(/price/i), '150.00');

    // Submit
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        symbol: 'AAPL',
        quantity: 10,
        price: 150.00,
      });
    });
  });

  it('displays API error message', async () => {
    mockOnSubmit.mockRejectedValueOnce(
      new Error('Insufficient balance')
    );

    const user = userEvent.setup();
    render(<OrderForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
    await user.type(screen.getByLabelText(/quantity/i), '1000');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText(/insufficient balance/i)).toBeInTheDocument();
    });
  });
});
```

#### 3. API 연동 컴포넌트 테스트 (MSW)

```typescript
// src/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/portfolio', (req, res, ctx) => {
    return res(
      ctx.json({
        totalValue: 11500,
        positions: [
          {
            symbol: 'AAPL',
            quantity: 10,
            avgPrice: 150,
            currentPrice: 160,
            unrealizedPnl: 100,
          },
        ],
      })
    );
  }),

  rest.post('/api/orders', (req, res, ctx) => {
    return res(
      ctx.json({
        id: '123',
        symbol: 'AAPL',
        status: 'pending',
      })
    );
  }),
];

// __tests__/components/Portfolio.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Portfolio } from '@/components/Portfolio';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

describe('Portfolio', () => {
  it('displays portfolio data', async () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <Portfolio />
      </QueryClientProvider>
    );

    // Loading state
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // Data loaded
    await waitFor(() => {
      expect(screen.getByText(/aapl/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/\$11,500/)).toBeInTheDocument();
    expect(screen.getByText(/10/)).toBeInTheDocument(); // quantity
    expect(screen.getByText(/\$100/)).toBeInTheDocument(); // PnL
  });
});
```

---

## E2E 테스트

### Playwright 설정

```javascript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',

  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### E2E 테스트 예제

```typescript
// e2e/trading-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Trading Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 로그인
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });

  test('complete buy order flow', async ({ page }) => {
    // 주문 페이지 이동
    await page.click('text=New Order');
    await expect(page).toHaveURL('/orders/new');

    // 주문 폼 작성
    await page.fill('[name="symbol"]', 'AAPL');
    await page.fill('[name="quantity"]', '10');
    await page.fill('[name="price"]', '150.00');
    await page.click('button:has-text("Buy")');

    // 확인 모달
    await expect(page.locator('text=Confirm Order')).toBeVisible();
    await page.click('button:has-text("Confirm")');

    // 성공 메시지
    await expect(page.locator('text=Order placed successfully')).toBeVisible();

    // 주문 목록에서 확인
    await page.click('text=Orders');
    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=PENDING')).toBeVisible();
  });

  test('portfolio displays positions', async ({ page }) => {
    await page.click('text=Portfolio');

    // 포트폴리오 요약
    await expect(page.locator('[data-testid="total-value"]')).toBeVisible();

    // 보유 종목
    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=10 shares')).toBeVisible();
  });

  test('real-time price update', async ({ page }) => {
    await page.goto('/market/AAPL');

    const priceElement = page.locator('[data-testid="current-price"]');
    const initialPrice = await priceElement.textContent();

    // Wait for WebSocket update (max 10 seconds)
    await page.waitForTimeout(10000);

    const updatedPrice = await priceElement.textContent();

    // Price should update (or at least element exists)
    expect(updatedPrice).toBeTruthy();
  });

  test('handles API error gracefully', async ({ page }) => {
    // Intercept API to return error
    await page.route('/api/orders', (route) => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({ detail: 'Insufficient balance' }),
      });
    });

    await page.goto('/orders/new');
    await page.fill('[name="symbol"]', 'TSLA');
    await page.fill('[name="quantity"]', '1000');
    await page.click('button:has-text("Buy")');

    // Error message displayed
    await expect(
      page.locator('text=Insufficient balance')
    ).toBeVisible();
  });
});

// e2e/auth.spec.ts
test.describe('Authentication', () => {
  test('login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome')).toBeVisible();
  });

  test('login with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL('/login');
  });

  test('protected route redirects to login', async ({ page }) => {
    await page.goto('/orders');

    await expect(page).toHaveURL('/login');
  });
});
```

---

## CI/CD 통합

### GitHub Actions 워크플로우

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_trading
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          cd backend
          pytest tests/unit -v --cov=src --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_trading
          REDIS_URL: redis://localhost:6379
        run: |
          cd backend
          pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Start services
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 10

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/

      - name: Stop services
        if: always()
        run: docker-compose -f docker-compose.test.yml down
```

---

## 실전 예제

### 시나리오: 주문 처리 전체 플로우 TDD

#### 1단계: 테스트 작성 (Red)

```python
# tests/integration/test_order_flow.py
def test_complete_order_flow(client, test_account, auth_headers):
    """주문 생성 → 체결 → 포트폴리오 업데이트 전체 플로우"""
    # Given: 초기 잔고 10,000
    initial_balance = 10000.0

    # When: 매수 주문 생성
    response = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            "account_id": test_account.id,
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "price": 150.0
        }
    )

    # Then: 주문 생성 성공
    assert response.status_code == 201
    order_id = response.json()["id"]

    # When: 주문 체결 (시뮬레이터)
    response = client.post(f"/api/orders/{order_id}/execute")

    # Then: 체결 성공
    assert response.status_code == 200

    # Then: 포트폴리오 업데이트 확인
    response = client.get("/api/portfolio", headers=auth_headers)
    portfolio = response.json()

    assert portfolio["cash_balance"] == 8500.0  # 10000 - 1500
    assert len(portfolio["positions"]) == 1
    assert portfolio["positions"][0]["symbol"] == "AAPL"
    assert portfolio["positions"][0]["quantity"] == 10
```

#### 2단계: 코드 작성 (Green)

```python
# src/trading/router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/orders")

@router.post("", status_code=201)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 계좌 확인
    account = db.query(Account).get(order_data.account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    # 잔고 확인
    required_amount = order_data.quantity * order_data.price
    if account.balance < required_amount:
        raise HTTPException(400, "Insufficient balance")

    # 주문 생성
    order = Order(
        account_id=account.id,
        symbol=order_data.symbol,
        side=order_data.side,
        quantity=order_data.quantity,
        price=order_data.price,
        status="pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order

@router.post("/{order_id}/execute")
def execute_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(404, "Order not found")

    if order.status != "pending":
        raise HTTPException(400, "Order already processed")

    # 시뮬레이터 체결
    account = order.account

    if order.side == "buy":
        # 잔고 차감
        account.balance -= order.quantity * order.price

        # 포지션 생성/업데이트
        position = db.query(Position).filter_by(
            account_id=account.id,
            symbol=order.symbol
        ).first()

        if position:
            # 평균 매입가 업데이트
            total_quantity = position.quantity + order.quantity
            total_cost = (
                position.quantity * position.avg_price +
                order.quantity * order.price
            )
            position.avg_price = total_cost / total_quantity
            position.quantity = total_quantity
        else:
            # 새 포지션 생성
            position = Position(
                account_id=account.id,
                symbol=order.symbol,
                quantity=order.quantity,
                avg_price=order.price
            )
            db.add(position)

    # 주문 상태 업데이트
    order.status = "filled"
    order.filled_at = datetime.now()

    db.commit()

    return {"status": "success", "order": order}
```

#### 3단계: 리팩토링 (Refactor)

```python
# src/trading/service.py
class TradingService:
    """거래 서비스 (비즈니스 로직 분리)"""

    def __init__(self, db: Session):
        self.db = db

    def create_order(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal
    ) -> Order:
        """주문 생성"""
        account = self._get_account(account_id)
        self._validate_balance(account, quantity, price)

        order = Order(
            account_id=account.id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING
        )

        self.db.add(order)
        self.db.commit()

        return order

    def execute_order(self, order_id: str) -> Order:
        """주문 체결"""
        order = self._get_order(order_id)
        self._validate_order_status(order)

        with self.db.begin_nested():  # Savepoint for rollback
            if order.side == "buy":
                self._execute_buy_order(order)
            else:
                self._execute_sell_order(order)

            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()

        self.db.commit()
        return order

    def _execute_buy_order(self, order: Order):
        """매수 주문 실행"""
        account = order.account
        total_cost = order.quantity * order.price

        # 잔고 차감
        account.balance -= total_cost

        # 포지션 업데이트
        position = self._get_or_create_position(
            account.id, order.symbol
        )

        # 평균 매입가 계산
        new_quantity = position.quantity + order.quantity
        new_avg_price = (
            (position.quantity * position.avg_price +
             order.quantity * order.price) / new_quantity
        )

        position.quantity = new_quantity
        position.avg_price = new_avg_price

    def _validate_balance(
        self, account: Account, quantity: int, price: Decimal
    ):
        """잔고 검증"""
        required = quantity * price
        if account.balance < required:
            raise InsufficientBalanceError(
                f"Required: {required}, Available: {account.balance}"
            )
```

---

## 테스트 커버리지 목표

### 목표 커버리지

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| **전체** | 80% | pytest --cov |
| **비즈니스 로직** | 90% | 핵심 서비스 |
| **API 엔드포인트** | 85% | 주요 API |
| **프론트엔드** | 70% | Jest |

### 커버리지 확인

```bash
# Backend
cd backend
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

---

## 베스트 프랙티스

### 1. 테스트 작성 원칙

```yaml
FIRST:
  - Fast: 빠르게 실행
  - Independent: 독립적
  - Repeatable: 반복 가능
  - Self-Validating: 자가 검증
  - Timely: 적시에 작성

AAA 패턴:
  - Arrange: 준비
  - Act: 실행
  - Assert: 검증

Given-When-Then:
  - Given: 초기 상태
  - When: 액션 실행
  - Then: 결과 검증
```

### 2. 테스트 명명 규칙

```python
# Good
def test_calculate_roi_returns_positive_value_when_profit():
    pass

def test_create_order_raises_error_when_insufficient_balance():
    pass

# Bad
def test_roi():
    pass

def test_order():
    pass
```

### 3. Mock 사용 가이드

```python
# Good: 외부 의존성만 Mock
@patch('src.market_data.service.MarketDataService.get_price')
def test_with_mock(mock_get_price):
    mock_get_price.return_value = 150.0
    # 테스트 로직

# Bad: 내부 로직까지 Mock (테스트 의미 없음)
@patch('src.trading.service.TradingService.calculate_total')
def test_bad_mock(mock_calculate):
    mock_calculate.return_value = 1500
    # 실제로 테스트하는 것이 없음
```

---

## 요약

### TDD 체크리스트

```yaml
개발 전:
  - [ ] 요구사항 명확히 정의
  - [ ] 테스트 케이스 작성 (Red)
  - [ ] 테스트 실행 (실패 확인)

개발 중:
  - [ ] 최소한의 코드 작성 (Green)
  - [ ] 테스트 통과 확인
  - [ ] 리팩토링 (Refactor)
  - [ ] 테스트 여전히 통과 확인

개발 후:
  - [ ] 커버리지 80% 이상
  - [ ] CI 통과
  - [ ] 코드 리뷰
```

### 다음 단계

1. **Unit Tests 작성**
   - 핵심 비즈니스 로직부터
   - 커버리지 90% 목표

2. **Integration Tests 추가**
   - API 엔드포인트
   - DB 연동

3. **E2E Tests 구축**
   - 주요 플로우 5-10개
   - CI에서 자동 실행

4. **지속적 개선**
   - 테스트 리팩토링
   - Flaky 테스트 제거
   - 실행 속도 최적화

---

**작성일**: 2026-02-07
**버전**: 1.0
**다음 업데이트**: 테스트 실행 후 개선사항 반영
