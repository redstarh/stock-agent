# 리팩토링 전략 가이드

> **목적**: 코드 품질 개선 및 유지보수성 향상을 위한 체계적 리팩토링 전략
> **대상**: Claude Code Teams를 활용한 독립적 Task 기반 리팩토링

---

## 📋 목차

1. [리팩토링 원칙](#리팩토링-원칙)
2. [언제 리팩토링을 해야 하는가](#언제-리팩토링을-해야-하는가)
3. [리팩토링 기법](#리팩토링-기법)
4. [SOLID 원칙](#solid-원칙)
5. [Claude Teams 워크플로우](#claude-teams-워크플로우)
6. [체크리스트](#체크리스트)
7. [자동화 도구](#자동화-도구)
8. [실전 예제](#실전-예제)

---

## 리팩토링 원칙

### 기본 원칙

```yaml
Red-Green-Refactor:
  1. Red: 테스트 작성 (실패)
  2. Green: 테스트 통과하는 코드 작성
  3. Refactor: 코드 개선 (테스트는 그대로)

핵심 규칙:
  - 동작을 변경하지 않음 (기능 추가 X)
  - 작은 단계로 진행
  - 각 단계마다 테스트 실행
  - 커밋을 자주 함
  - 리팩토링 전 테스트 커버리지 확보
```

### 리팩토링 vs 재작성

| 항목 | 리팩토링 | 재작성 |
|------|---------|--------|
| **동작 변경** | ❌ 없음 | ✅ 가능 |
| **테스트** | ✅ 기존 유지 | ⚠️ 재작성 필요 |
| **리스크** | 낮음 | 높음 |
| **시간** | 단계적 | 대규모 |
| **배포** | 즉시 가능 | 완료 후 |

**원칙**: 재작성은 최후의 수단. 가능한 한 리팩토링으로 해결

---

## 언제 리팩토링을 해야 하는가

### Code Smells (나쁜 코드의 징후)

#### 1. **긴 메서드** (Long Method)
```python
# Bad: 100줄 이상의 메서드
def process_order(order_data):
    # 검증 (20줄)
    # 계산 (30줄)
    # DB 저장 (20줄)
    # 알림 발송 (30줄)
    pass  # 100+ lines
```

**징후**:
- 메서드가 화면을 넘어감
- 여러 가지 일을 함
- 주석으로 섹션을 구분함

**기준**: 메서드는 **15줄 이내** (이상적으로는 10줄)

---

#### 2. **중복 코드** (Duplicated Code)
```python
# Bad: 같은 로직이 여러 곳에
def calculate_buy_commission(amount):
    return amount * 0.001

def calculate_sell_commission(amount):
    return amount * 0.001  # 중복!
```

**징후**:
- Copy & Paste로 코드 작성
- 유사한 코드가 2개 이상
- 한 곳 수정 시 다른 곳도 수정 필요

**기준**: **DRY 원칙** (Don't Repeat Yourself)

---

#### 3. **매직 넘버/문자열** (Magic Numbers)
```python
# Bad
if order.quantity > 1000:  # 1000이 뭐지?
    discount = price * 0.05  # 5%? 왜?
```

**징후**:
- 숫자/문자열의 의미가 불명확
- 같은 값이 여러 곳에 하드코딩

**기준**: 모든 상수는 **명명된 상수**로 추출

---

#### 4. **거대한 클래스** (Large Class)
```python
# Bad: 한 클래스가 너무 많은 책임
class TradingService:
    def create_order(self): pass
    def execute_order(self): pass
    def calculate_commission(self): pass
    def send_notification(self): pass
    def generate_report(self): pass
    def validate_risk(self): pass
    # ... 20+ methods
```

**징후**:
- 클래스가 500줄 이상
- 10개 이상의 메서드
- 여러 역할을 수행

**기준**: 클래스는 **하나의 책임**만 (SRP)

---

#### 5. **긴 파라미터 목록** (Long Parameter List)
```python
# Bad
def create_order(symbol, quantity, price, side, order_type,
                 account_id, user_id, stop_loss, take_profit,
                 time_in_force, client_order_id):
    pass  # 11개 파라미터!
```

**징후**:
- 파라미터가 5개 이상
- 파라미터 순서를 기억하기 어려움

**기준**: 파라미터는 **3개 이하** (또는 DTO 사용)

---

#### 6. **복잡한 조건문** (Complex Conditional)
```python
# Bad
if (order.status == "pending" and order.quantity > 0 and
    account.balance >= order.quantity * order.price and
    not risk_limit_exceeded and market_open and
    order.symbol in allowed_symbols):
    execute_order(order)
```

**징후**:
- 중첩된 if 문
- 긴 boolean 표현식
- 이해하기 어려운 조건

**기준**: 조건문은 **2단계 이내** 중첩

---

### 리팩토링 트리거

```yaml
언제 리팩토링을 시작하는가:

즉시:
  - 코드 리뷰에서 지적됨
  - Code smell 발견 시
  - 버그 수정 중 난해한 코드 발견

계획적:
  - Sprint 종료 후
  - 기능 개발 전
  - 성능 개선 필요 시

주기적:
  - 매주 금요일 오후
  - Technical Debt 상환 주간
  - 2주마다 리팩토링 Task
```

---

## 리팩토링 기법

### 1. 메서드 추출 (Extract Method)

**Before**:
```python
def process_order(order_data):
    # 검증
    if not order_data.get('symbol'):
        raise ValueError("Symbol required")
    if order_data.get('quantity', 0) <= 0:
        raise ValueError("Invalid quantity")
    if not order_data.get('price'):
        raise ValueError("Price required")

    # 계산
    total = order_data['quantity'] * order_data['price']
    commission = total * 0.001
    total_with_commission = total + commission

    # 저장
    order = Order(**order_data)
    order.total = total_with_commission
    db.session.add(order)
    db.session.commit()

    return order
```

**After**:
```python
def process_order(order_data):
    validate_order_data(order_data)
    total = calculate_order_total(order_data)
    order = save_order(order_data, total)
    return order

def validate_order_data(data):
    """주문 데이터 검증"""
    if not data.get('symbol'):
        raise ValueError("Symbol required")
    if data.get('quantity', 0) <= 0:
        raise ValueError("Invalid quantity")
    if not data.get('price'):
        raise ValueError("Price required")

def calculate_order_total(data):
    """주문 총액 계산 (수수료 포함)"""
    subtotal = data['quantity'] * data['price']
    commission = subtotal * COMMISSION_RATE
    return subtotal + commission

def save_order(data, total):
    """주문 저장"""
    order = Order(**data)
    order.total = total
    db.session.add(order)
    db.session.commit()
    return order
```

**효과**:
- ✅ 각 메서드가 하나의 역할
- ✅ 테스트 작성 용이
- ✅ 재사용 가능
- ✅ 가독성 향상

---

### 2. 중복 코드 제거 (Remove Duplication)

**Before**:
```python
class OrderService:
    def execute_buy_order(self, order):
        # 잔고 확인
        required = order.quantity * order.price
        if account.balance < required:
            raise InsufficientBalanceError()

        # 리스크 검증
        if self.check_daily_loss_limit():
            raise RiskLimitError()

        # 주문 실행
        account.balance -= required
        position = create_position(order)
        order.status = "filled"
        return order

    def execute_sell_order(self, order):
        # 포지션 확인
        position = get_position(order.symbol)
        if position.quantity < order.quantity:
            raise InsufficientPositionError()

        # 리스크 검증
        if self.check_daily_loss_limit():
            raise RiskLimitError()

        # 주문 실행
        proceeds = order.quantity * order.price
        account.balance += proceeds
        position.quantity -= order.quantity
        order.status = "filled"
        return order
```

**After**:
```python
class OrderService:
    def execute_order(self, order):
        self._validate_order(order)
        self._check_risk_limits()

        if order.side == "buy":
            self._execute_buy(order)
        else:
            self._execute_sell(order)

        order.status = "filled"
        return order

    def _validate_order(self, order):
        """주문 검증 (공통)"""
        if order.side == "buy":
            self._validate_balance(order)
        else:
            self._validate_position(order)

    def _check_risk_limits(self):
        """리스크 한도 검증 (공통)"""
        if self.check_daily_loss_limit():
            raise RiskLimitError()

    def _execute_buy(self, order):
        """매수 실행"""
        required = order.quantity * order.price
        self.account.balance -= required
        create_position(order)

    def _execute_sell(self, order):
        """매도 실행"""
        proceeds = order.quantity * order.price
        self.account.balance += proceeds
        update_position(order)
```

**효과**:
- ✅ 중복 제거
- ✅ 유지보수 용이
- ✅ 버그 감소

---

### 3. 매직 넘버 제거 (Replace Magic Numbers)

**Before**:
```python
def calculate_commission(amount):
    return amount * 0.001

def check_large_order(quantity):
    return quantity > 1000

def apply_discount(price):
    if price > 100000:
        return price * 0.95
    return price
```

**After**:
```python
# constants.py
COMMISSION_RATE = Decimal("0.001")  # 0.1%
LARGE_ORDER_THRESHOLD = 1000
BULK_DISCOUNT_THRESHOLD = Decimal("100000")
BULK_DISCOUNT_RATE = Decimal("0.05")  # 5% 할인

# service.py
def calculate_commission(amount: Decimal) -> Decimal:
    """거래 수수료 계산 (0.1%)"""
    return amount * COMMISSION_RATE

def check_large_order(quantity: int) -> bool:
    """대량 주문 여부 (1,000주 이상)"""
    return quantity > LARGE_ORDER_THRESHOLD

def apply_discount(price: Decimal) -> Decimal:
    """대량 거래 할인 적용 (10만원 이상 5% 할인)"""
    if price > BULK_DISCOUNT_THRESHOLD:
        return price * (1 - BULK_DISCOUNT_RATE)
    return price
```

**효과**:
- ✅ 의미 명확
- ✅ 변경 용이
- ✅ 문서화 역할

---

### 4. 조건문 단순화 (Simplify Conditionals)

**Before**:
```python
def can_execute_order(order, account, market):
    if order.status == "pending":
        if order.quantity > 0:
            required = order.quantity * order.price
            if account.balance >= required:
                if market.is_open:
                    if not is_risk_limit_exceeded(account):
                        return True
    return False
```

**After**:
```python
def can_execute_order(order, account, market):
    """주문 실행 가능 여부"""
    if not is_order_valid(order):
        return False

    if not has_sufficient_balance(account, order):
        return False

    if not market.is_open:
        return False

    if is_risk_limit_exceeded(account):
        return False

    return True

def is_order_valid(order):
    """주문 유효성 검증"""
    return order.status == "pending" and order.quantity > 0

def has_sufficient_balance(account, order):
    """잔고 충분 여부"""
    required = order.quantity * order.price
    return account.balance >= required
```

**또는 Guard Clauses 사용**:
```python
def can_execute_order(order, account, market):
    """주문 실행 가능 여부 (Guard Clauses)"""
    # Early returns로 명확하게
    if order.status != "pending":
        return False

    if order.quantity <= 0:
        return False

    required = order.quantity * order.price
    if account.balance < required:
        return False

    if not market.is_open:
        return False

    if is_risk_limit_exceeded(account):
        return False

    return True
```

**효과**:
- ✅ 가독성 향상
- ✅ 중첩 감소
- ✅ 조기 반환 (Early Return)

---

### 5. 클래스 추출 (Extract Class)

**Before**:
```python
class Order:
    def __init__(self, symbol, quantity, price, side):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.side = side
        self.status = "pending"
        self.created_at = datetime.now()

    def calculate_total(self):
        return self.quantity * self.price

    def calculate_commission(self):
        return self.calculate_total() * 0.001

    def calculate_tax(self):
        return self.calculate_total() * 0.003

    def get_total_cost(self):
        return (self.calculate_total() +
                self.calculate_commission() +
                self.calculate_tax())

    def validate_quantity(self):
        return self.quantity > 0

    def validate_price(self):
        return self.price > 0

    def is_buy_order(self):
        return self.side == "buy"
```

**After**:
```python
class Order:
    """주문 엔티티"""
    def __init__(self, symbol, quantity, price, side):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.side = side
        self.status = "pending"
        self.created_at = datetime.now()

    def is_buy_order(self):
        return self.side == "buy"


class OrderCalculator:
    """주문 금액 계산"""
    def __init__(self, order: Order):
        self.order = order

    def calculate_subtotal(self) -> Decimal:
        return self.order.quantity * self.order.price

    def calculate_commission(self) -> Decimal:
        return self.calculate_subtotal() * COMMISSION_RATE

    def calculate_tax(self) -> Decimal:
        return self.calculate_subtotal() * TAX_RATE

    def get_total_cost(self) -> Decimal:
        return (self.calculate_subtotal() +
                self.calculate_commission() +
                self.calculate_tax())


class OrderValidator:
    """주문 검증"""
    def __init__(self, order: Order):
        self.order = order

    def validate(self) -> bool:
        return (self.validate_quantity() and
                self.validate_price())

    def validate_quantity(self) -> bool:
        return self.order.quantity > 0

    def validate_price(self) -> bool:
        return self.order.price > 0
```

**효과**:
- ✅ 단일 책임 원칙 (SRP)
- ✅ 테스트 용이
- ✅ 확장 가능

---

### 6. 파라미터 객체 도입 (Introduce Parameter Object)

**Before**:
```python
def create_order(symbol, quantity, price, side, order_type,
                 account_id, stop_loss, take_profit):
    # 8개 파라미터...
    pass

def validate_order(symbol, quantity, price, side, account_id):
    # 5개 파라미터...
    pass
```

**After**:
```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class OrderRequest:
    """주문 요청 DTO"""
    symbol: str
    quantity: int
    price: Decimal
    side: str
    order_type: str
    account_id: str
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None

def create_order(request: OrderRequest) -> Order:
    validate_order(request)
    return Order(**request.__dict__)

def validate_order(request: OrderRequest) -> None:
    if not request.symbol:
        raise ValueError("Symbol required")
    # ...
```

**효과**:
- ✅ 파라미터 관리 용이
- ✅ 타입 안전성
- ✅ 확장 용이

---

## SOLID 원칙

### S - Single Responsibility Principle (단일 책임 원칙)

**원칙**: 클래스는 하나의 책임만 가져야 함

**Before**:
```python
class OrderService:
    """모든 것을 처리 (나쁜 예)"""
    def create_order(self, data):
        # 검증
        if not self._validate(data):
            raise ValueError()

        # 저장
        order = Order(**data)
        self.db.save(order)

        # 이메일 발송
        self.send_email(order)

        # 로그 기록
        self.log(f"Order created: {order.id}")

        return order
```

**After**:
```python
class OrderService:
    """주문 비즈니스 로직만"""
    def __init__(self, repository, validator, notifier):
        self.repository = repository
        self.validator = validator
        self.notifier = notifier

    def create_order(self, data):
        self.validator.validate(data)
        order = Order(**data)
        self.repository.save(order)
        self.notifier.notify_order_created(order)
        return order

class OrderValidator:
    """검증만"""
    def validate(self, data):
        # 검증 로직
        pass

class OrderRepository:
    """DB 저장만"""
    def save(self, order):
        # 저장 로직
        pass

class OrderNotifier:
    """알림만"""
    def notify_order_created(self, order):
        # 이메일/SMS 발송
        pass
```

---

### O - Open/Closed Principle (개방/폐쇄 원칙)

**원칙**: 확장에는 열려있고, 수정에는 닫혀있어야 함

**Before**:
```python
class CommissionCalculator:
    def calculate(self, order, account_type):
        if account_type == "basic":
            return order.total * 0.001
        elif account_type == "premium":
            return order.total * 0.0005
        elif account_type == "vip":
            return 0
        # 새 타입 추가 시 이 메서드 수정 필요!
```

**After**:
```python
from abc import ABC, abstractmethod

class CommissionStrategy(ABC):
    @abstractmethod
    def calculate(self, order):
        pass

class BasicCommission(CommissionStrategy):
    def calculate(self, order):
        return order.total * 0.001

class PremiumCommission(CommissionStrategy):
    def calculate(self, order):
        return order.total * 0.0005

class VIPCommission(CommissionStrategy):
    def calculate(self, order):
        return 0

class CommissionCalculator:
    def __init__(self, strategy: CommissionStrategy):
        self.strategy = strategy

    def calculate(self, order):
        return self.strategy.calculate(order)

# 사용
calculator = CommissionCalculator(PremiumCommission())
commission = calculator.calculate(order)

# 새 타입 추가 시 새 클래스만 생성 (기존 코드 수정 X)
```

---

### L - Liskov Substitution Principle (리스코프 치환 원칙)

**원칙**: 자식 클래스는 부모 클래스를 대체할 수 있어야 함

**Before**:
```python
class Order:
    def execute(self):
        # 주문 실행
        pass

class MarketOrder(Order):
    def execute(self):
        # 시장가 주문 실행
        pass

class LimitOrder(Order):
    def execute(self):
        # 지정가 주문 실행
        pass

class InvalidOrder(Order):
    def execute(self):
        raise NotImplementedError("Cannot execute invalid order")
        # 부모 계약 위반!
```

**After**:
```python
from abc import ABC, abstractmethod

class Order(ABC):
    @abstractmethod
    def can_execute(self) -> bool:
        pass

    @abstractmethod
    def execute(self):
        pass

class MarketOrder(Order):
    def can_execute(self) -> bool:
        return True

    def execute(self):
        # 항상 실행 가능
        pass

class LimitOrder(Order):
    def can_execute(self) -> bool:
        return self.current_price <= self.limit_price

    def execute(self):
        if self.can_execute():
            # 실행
            pass

# InvalidOrder는 Order를 상속하지 않음
class InvalidOrder:
    pass
```

---

### I - Interface Segregation Principle (인터페이스 분리 원칙)

**원칙**: 클라이언트는 사용하지 않는 메서드에 의존하지 않아야 함

**Before**:
```python
class TradingInterface(ABC):
    @abstractmethod
    def place_order(self): pass

    @abstractmethod
    def cancel_order(self): pass

    @abstractmethod
    def get_real_time_price(self): pass

    @abstractmethod
    def get_historical_data(self): pass

    @abstractmethod
    def subscribe_to_feed(self): pass

class SimpleTradingClient(TradingInterface):
    def place_order(self):
        # 구현
        pass

    def cancel_order(self):
        # 구현
        pass

    # 사용하지 않지만 구현해야 함
    def get_real_time_price(self):
        raise NotImplementedError()

    def get_historical_data(self):
        raise NotImplementedError()

    def subscribe_to_feed(self):
        raise NotImplementedError()
```

**After**:
```python
class OrderManagement(ABC):
    @abstractmethod
    def place_order(self): pass

    @abstractmethod
    def cancel_order(self): pass

class MarketData(ABC):
    @abstractmethod
    def get_real_time_price(self): pass

    @abstractmethod
    def get_historical_data(self): pass

class StreamingData(ABC):
    @abstractmethod
    def subscribe_to_feed(self): pass

class SimpleTradingClient(OrderManagement):
    """주문 관리만"""
    def place_order(self):
        pass

    def cancel_order(self):
        pass

class AdvancedTradingClient(OrderManagement, MarketData, StreamingData):
    """모든 기능"""
    def place_order(self): pass
    def cancel_order(self): pass
    def get_real_time_price(self): pass
    def get_historical_data(self): pass
    def subscribe_to_feed(self): pass
```

---

### D - Dependency Inversion Principle (의존성 역전 원칙)

**원칙**: 구체화가 아닌 추상화에 의존해야 함

**Before**:
```python
class OrderService:
    def __init__(self):
        self.db = PostgreSQLDatabase()  # 구체 클래스에 의존
        self.email = GmailSender()      # 구체 클래스에 의존

    def create_order(self, data):
        order = Order(**data)
        self.db.save(order)
        self.email.send(order.user.email, "Order created")
```

**After**:
```python
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order): pass

class EmailSender(ABC):
    @abstractmethod
    def send(self, to, message): pass

class OrderService:
    def __init__(self,
                 repository: OrderRepository,
                 email_sender: EmailSender):
        self.repository = repository
        self.email_sender = email_sender

    def create_order(self, data):
        order = Order(**data)
        self.repository.save(order)
        self.email_sender.send(order.user.email, "Order created")

# 구현체
class PostgreSQLRepository(OrderRepository):
    def save(self, order):
        # PostgreSQL 저장
        pass

class GmailSender(EmailSender):
    def send(self, to, message):
        # Gmail 발송
        pass

# 주입
service = OrderService(
    PostgreSQLRepository(),
    GmailSender()
)

# 테스트 시 Mock 주입 가능
service_test = OrderService(
    MockRepository(),
    MockEmailSender()
)
```

---

## Claude Teams 워크플로우

### 리팩토링 Task 생성

```yaml
Task Template:
  Title: "refactor: [대상] - [기법]"

  Examples:
    - "refactor: OrderService - Extract methods"
    - "refactor: Remove magic numbers from commission calculation"
    - "refactor: Apply SRP to TradingService"
    - "refactor: Simplify order validation conditionals"

  Description:
    - 현재 문제점 (Code Smell)
    - 리팩토링 목표
    - 적용할 기법
    - 성공 기준

  Labels:
    - refactoring
    - tech-debt
    - [component] (backend/frontend)

  Acceptance Criteria:
    - [ ] 모든 테스트 통과
    - [ ] 커버리지 유지/향상
    - [ ] Code smell 제거
    - [ ] 코드 리뷰 승인
```

### Task 예시

```markdown
## Task: refactor: OrderService - Extract methods

### Problem (Code Smell)
- `process_order()` 메서드가 150줄 (Long Method)
- 여러 책임을 가짐 (검증, 계산, 저장, 알림)
- 테스트 어려움

### Refactoring Goal
- 메서드를 역할별로 분리
- 각 메서드 15줄 이내
- 단위 테스트 작성 용이하게

### Techniques
1. Extract Method
2. Single Responsibility Principle

### Steps
1. [ ] 테스트 커버리지 확인 (현재: 65%)
2. [ ] `validate_order_data()` 추출
3. [ ] `calculate_order_total()` 추출
4. [ ] `save_order()` 추출
5. [ ] `notify_order_created()` 추출
6. [ ] 테스트 실행 및 확인
7. [ ] 커버리지 확인 (목표: 80%+)

### Success Criteria
- [x] 모든 기존 테스트 통과
- [ ] `process_order()` 메서드 15줄 이내
- [ ] 각 추출된 메서드에 단위 테스트 추가
- [ ] 커버리지 80% 이상
- [ ] Code review 승인

### Time Estimate
2-3 hours
```

---

### Team 역할 분담

```yaml
Refactoring Lead:
  - 리팩토링 계획 수립
  - Code smell 식별
  - Task 우선순위 결정

Backend Refactoring Agent:
  - Backend 코드 리팩토링
  - 테스트 작성/수정
  - 성능 측정

Frontend Refactoring Agent:
  - Frontend 코드 리팩토링
  - 컴포넌트 분리
  - 접근성 개선

QA Agent:
  - 리팩토링 전후 테스트
  - 회귀 테스트
  - 성능 비교

Code Reviewer:
  - 리팩토링 코드 리뷰
  - SOLID 원칙 준수 확인
  - 베스트 프랙티스 제안
```

---

## 체크리스트

### 리팩토링 전 (Pre-Refactoring)

```markdown
- [ ] 리팩토링 대상 명확히 정의
- [ ] 현재 테스트 커버리지 확인
- [ ] 모든 테스트 통과 확인
- [ ] 리팩토링 범위 결정 (작게 시작)
- [ ] Git branch 생성
- [ ] Baseline 커밋 생성
```

### 리팩토링 중 (During Refactoring)

```markdown
- [ ] 한 번에 하나의 기법만 적용
- [ ] 각 단계마다 테스트 실행
- [ ] 자주 커밋 (작은 단위)
- [ ] 동작 변경 없음 확인
- [ ] 성능 저하 없음 확인
```

### 리팩토링 후 (Post-Refactoring)

```markdown
- [ ] 모든 테스트 통과
- [ ] 커버리지 유지/향상
- [ ] 코드 리뷰 요청
- [ ] CI/CD 통과
- [ ] 문서 업데이트
- [ ] CHANGELOG 작성
```

---

## 자동화 도구

### Python (Backend)

```yaml
Formatting:
  - black: 코드 포맷팅
  - isort: import 정렬

Linting:
  - flake8: 스타일 체크
  - pylint: 정적 분석
  - mypy: 타입 체크

Code Quality:
  - radon: 복잡도 측정
  - bandit: 보안 취약점 검사

Refactoring Tools:
  - rope: 자동 리팩토링
```

#### 설정 파일

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.pylint.messages_control]
max-line-length = 88
disable = ["C0111", "C0103"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

#### 실행 스크립트

```bash
#!/bin/bash
# refactor-check.sh

echo "🔍 Checking code quality..."

# 포맷 체크
black --check backend/src/
isort --check-only backend/src/

# Lint
flake8 backend/src/
pylint backend/src/

# 타입 체크
mypy backend/src/

# 복잡도 측정
radon cc backend/src/ -a -nb

# 보안 체크
bandit -r backend/src/

echo "✅ All checks passed!"
```

---

### TypeScript (Frontend)

```yaml
Formatting:
  - prettier: 코드 포맷팅

Linting:
  - eslint: 스타일 체크
  - typescript-eslint: TS 체크

Code Quality:
  - eslint-plugin-complexity: 복잡도 체크
```

#### 설정 파일

```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "prettier"
  ],
  "rules": {
    "complexity": ["error", 10],
    "max-lines-per-function": ["error", 50],
    "max-depth": ["error", 3],
    "max-params": ["error", 3]
  }
}
```

---

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
```

설치:
```bash
pip install pre-commit
pre-commit install
```

---

## 실전 예제

### 예제 1: 긴 메서드 리팩토링

#### Before (문제점)
```python
def process_order(self, order_data: dict) -> Order:
    """주문 처리 (150줄)"""
    # 검증 (30줄)
    if not order_data.get('symbol'):
        raise ValueError("Symbol is required")
    if not order_data.get('quantity'):
        raise ValueError("Quantity is required")
    if order_data['quantity'] <= 0:
        raise ValueError("Quantity must be positive")
    if not order_data.get('price'):
        raise ValueError("Price is required")
    if order_data['price'] <= 0:
        raise ValueError("Price must be positive")
    if order_data.get('side') not in ['buy', 'sell']:
        raise ValueError("Invalid side")

    # 계좌 확인 (20줄)
    account = self.db.query(Account).get(order_data['account_id'])
    if not account:
        raise ValueError("Account not found")
    if not account.is_active:
        raise ValueError("Account is not active")

    # 잔고 확인 (15줄)
    if order_data['side'] == 'buy':
        required = order_data['quantity'] * order_data['price']
        commission = required * 0.001
        total_required = required + commission
        if account.balance < total_required:
            raise ValueError("Insufficient balance")

    # 포지션 확인 (15줄)
    if order_data['side'] == 'sell':
        position = self.db.query(Position).filter_by(
            account_id=account.id,
            symbol=order_data['symbol']
        ).first()
        if not position:
            raise ValueError("No position found")
        if position.quantity < order_data['quantity']:
            raise ValueError("Insufficient quantity")

    # 리스크 확인 (20줄)
    daily_loss = self.calculate_daily_loss(account)
    if daily_loss > account.max_daily_loss:
        raise ValueError("Daily loss limit exceeded")

    position_value = order_data['quantity'] * order_data['price']
    portfolio_value = self.calculate_portfolio_value(account)
    position_ratio = position_value / portfolio_value
    if position_ratio > 0.3:
        raise ValueError("Position size too large")

    # 주문 생성 (10줄)
    order = Order(
        account_id=account.id,
        symbol=order_data['symbol'],
        quantity=order_data['quantity'],
        price=order_data['price'],
        side=order_data['side'],
        status='pending'
    )
    self.db.add(order)
    self.db.commit()

    # 알림 발송 (20줄)
    try:
        self.send_email(
            account.user.email,
            f"Order created: {order.symbol}",
            self.render_template('order_created.html', order=order)
        )
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

    # 로그 (10줄)
    logger.info(f"Order created: {order.id}")
    self.audit_log.create(
        user_id=account.user_id,
        action='order_created',
        details={'order_id': order.id}
    )

    return order
```

#### After (리팩토링)

```python
# order_service.py
class OrderService:
    def __init__(self,
                 repository: OrderRepository,
                 validator: OrderValidator,
                 risk_manager: RiskManager,
                 notifier: OrderNotifier):
        self.repository = repository
        self.validator = validator
        self.risk_manager = risk_manager
        self.notifier = notifier

    def process_order(self, order_data: dict) -> Order:
        """주문 처리 (메인 플로우)"""
        # 1. 검증
        self.validator.validate_order_data(order_data)
        account = self.validator.validate_account(order_data['account_id'])
        self.validator.validate_balance(account, order_data)

        # 2. 리스크 확인
        self.risk_manager.check_limits(account, order_data)

        # 3. 주문 생성
        order = self._create_order(account, order_data)

        # 4. 알림
        self.notifier.notify_order_created(order)

        return order

    def _create_order(self, account: Account, data: dict) -> Order:
        """주문 엔티티 생성 및 저장"""
        order = Order(
            account_id=account.id,
            symbol=data['symbol'],
            quantity=data['quantity'],
            price=data['price'],
            side=data['side'],
            status=OrderStatus.PENDING
        )
        return self.repository.save(order)

# order_validator.py
class OrderValidator:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def validate_order_data(self, data: dict) -> None:
        """주문 데이터 검증"""
        self._validate_required_fields(data)
        self._validate_quantity(data['quantity'])
        self._validate_price(data['price'])
        self._validate_side(data['side'])

    def validate_account(self, account_id: str) -> Account:
        """계좌 검증"""
        account = self.repository.get_account(account_id)
        if not account:
            raise AccountNotFoundError()
        if not account.is_active:
            raise InactiveAccountError()
        return account

    def validate_balance(self, account: Account, data: dict) -> None:
        """잔고 검증"""
        if data['side'] == 'buy':
            self._validate_buy_balance(account, data)
        else:
            self._validate_sell_position(account, data)

    def _validate_required_fields(self, data: dict) -> None:
        """필수 필드 확인"""
        required = ['symbol', 'quantity', 'price', 'side']
        for field in required:
            if not data.get(field):
                raise ValueError(f"{field} is required")

    def _validate_quantity(self, quantity: int) -> None:
        """수량 검증"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

    def _validate_price(self, price: Decimal) -> None:
        """가격 검증"""
        if price <= 0:
            raise ValueError("Price must be positive")

    def _validate_side(self, side: str) -> None:
        """주문 방향 검증"""
        if side not in ['buy', 'sell']:
            raise ValueError("Invalid side")

    def _validate_buy_balance(self, account: Account, data: dict) -> None:
        """매수 잔고 검증"""
        calculator = OrderCalculator(data)
        total_required = calculator.get_total_cost()

        if account.balance < total_required:
            raise InsufficientBalanceError(
                f"Required: {total_required}, Available: {account.balance}"
            )

    def _validate_sell_position(self, account: Account, data: dict) -> None:
        """매도 포지션 검증"""
        position = self.repository.get_position(
            account.id, data['symbol']
        )

        if not position:
            raise NoPositionError(f"No position for {data['symbol']}")

        if position.quantity < data['quantity']:
            raise InsufficientQuantityError(
                f"Required: {data['quantity']}, Available: {position.quantity}"
            )

# risk_manager.py
class RiskManager:
    def __init__(self, config: RiskConfig):
        self.config = config

    def check_limits(self, account: Account, order_data: dict) -> None:
        """리스크 한도 확인"""
        self._check_daily_loss_limit(account)
        self._check_position_size_limit(account, order_data)

    def _check_daily_loss_limit(self, account: Account) -> None:
        """일일 손실 한도 확인"""
        daily_loss = self._calculate_daily_loss(account)
        max_loss = account.risk_limits.max_daily_loss

        if daily_loss > max_loss:
            raise DailyLossLimitError(
                f"Daily loss: {daily_loss}, Limit: {max_loss}"
            )

    def _check_position_size_limit(
        self, account: Account, order_data: dict
    ) -> None:
        """포지션 크기 한도 확인"""
        order_value = order_data['quantity'] * order_data['price']
        portfolio_value = self._calculate_portfolio_value(account)
        ratio = order_value / portfolio_value

        max_ratio = self.config.max_position_ratio
        if ratio > max_ratio:
            raise PositionSizeLimitError(
                f"Position ratio: {ratio:.2%}, Limit: {max_ratio:.2%}"
            )

    def _calculate_daily_loss(self, account: Account) -> Decimal:
        """일일 손실 계산"""
        # 구현...
        pass

    def _calculate_portfolio_value(self, account: Account) -> Decimal:
        """포트폴리오 평가액 계산"""
        # 구현...
        pass

# order_calculator.py
class OrderCalculator:
    """주문 금액 계산"""
    def __init__(self, order_data: dict):
        self.data = order_data

    def get_subtotal(self) -> Decimal:
        """소계"""
        return self.data['quantity'] * self.data['price']

    def get_commission(self) -> Decimal:
        """수수료"""
        return self.get_subtotal() * COMMISSION_RATE

    def get_total_cost(self) -> Decimal:
        """총 비용 (수수료 포함)"""
        return self.get_subtotal() + self.get_commission()

# order_notifier.py
class OrderNotifier:
    """주문 알림"""
    def __init__(self,
                 email_service: EmailService,
                 audit_logger: AuditLogger):
        self.email_service = email_service
        self.audit_logger = audit_logger

    def notify_order_created(self, order: Order) -> None:
        """주문 생성 알림"""
        self._send_email(order)
        self._log_audit(order)

    def _send_email(self, order: Order) -> None:
        """이메일 발송"""
        try:
            self.email_service.send(
                to=order.account.user.email,
                subject=f"Order created: {order.symbol}",
                template='order_created.html',
                context={'order': order}
            )
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def _log_audit(self, order: Order) -> None:
        """감사 로그 기록"""
        self.audit_logger.log(
            user_id=order.account.user_id,
            action='order_created',
            details={'order_id': order.id}
        )
```

#### 개선 효과

```yaml
Before:
  - Lines: 150줄
  - Methods: 1개
  - Responsibilities: 6개 (검증, 계산, 저장, 알림, 로그, 리스크)
  - Test Coverage: 65%
  - Cyclomatic Complexity: 25

After:
  - Lines: 평균 10줄/메서드
  - Classes: 5개
  - Responsibilities: 각 클래스 1개 (SRP)
  - Test Coverage: 90%
  - Cyclomatic Complexity: 평균 3

Benefits:
  - ✅ 가독성 향상
  - ✅ 테스트 용이
  - ✅ 재사용 가능
  - ✅ 확장 용이
  - ✅ 유지보수 쉬움
```

---

### 예제 2: 중복 코드 제거

#### Before
```python
class PortfolioService:
    def get_stock_portfolio(self, user_id):
        positions = db.query(Position).filter_by(
            user_id=user_id,
            asset_type='stock'
        ).all()

        total_value = 0
        for pos in positions:
            current_price = market_data.get_price(pos.symbol)
            value = pos.quantity * current_price
            total_value += value

        return {
            'positions': positions,
            'total_value': total_value
        }

    def get_crypto_portfolio(self, user_id):
        positions = db.query(Position).filter_by(
            user_id=user_id,
            asset_type='crypto'
        ).all()

        total_value = 0
        for pos in positions:
            current_price = market_data.get_price(pos.symbol)
            value = pos.quantity * current_price
            total_value += value

        return {
            'positions': positions,
            'total_value': total_value
        }
```

#### After
```python
class PortfolioService:
    def get_portfolio(self, user_id: str, asset_type: str) -> dict:
        """포트폴리오 조회 (공통)"""
        positions = self._get_positions(user_id, asset_type)
        total_value = self._calculate_total_value(positions)

        return {
            'positions': positions,
            'total_value': total_value
        }

    def get_stock_portfolio(self, user_id: str) -> dict:
        """주식 포트폴리오"""
        return self.get_portfolio(user_id, 'stock')

    def get_crypto_portfolio(self, user_id: str) -> dict:
        """암호화폐 포트폴리오"""
        return self.get_portfolio(user_id, 'crypto')

    def _get_positions(self, user_id: str, asset_type: str) -> List[Position]:
        """포지션 조회"""
        return db.query(Position).filter_by(
            user_id=user_id,
            asset_type=asset_type
        ).all()

    def _calculate_total_value(self, positions: List[Position]) -> Decimal:
        """총 평가액 계산"""
        total = Decimal(0)
        for pos in positions:
            current_price = market_data.get_price(pos.symbol)
            value = pos.quantity * current_price
            total += value
        return total
```

---

## 리팩토링 측정 지표

### 코드 메트릭

```yaml
Cyclomatic Complexity (순환 복잡도):
  - 1-5: 단순 (Good)
  - 6-10: 보통 (OK)
  - 11-20: 복잡 (Refactor)
  - 21+: 매우 복잡 (Must Refactor)

Lines of Code (코드 라인 수):
  - Method: 15줄 이하 (이상적: 10줄)
  - Class: 300줄 이하
  - File: 500줄 이하

Parameters:
  - 3개 이하 (이상적: 2개)

Test Coverage:
  - 80% 이상
```

### 측정 도구

```bash
# Python: radon
pip install radon

# 복잡도 측정
radon cc backend/src/ -a -nb

# 유지보수성 지수
radon mi backend/src/ -s

# 원시 메트릭 (LOC, LLOC, SLOC)
radon raw backend/src/ -s
```

---

## 참고 자료

### 책
- **Refactoring** by Martin Fowler
- **Clean Code** by Robert C. Martin
- **Working Effectively with Legacy Code** by Michael Feathers

### 온라인 리소스
- [Refactoring.Guru](https://refactoring.guru/)
- [SourceMaking - Refactoring](https://sourcemaking.com/refactoring)
- [Martin Fowler's Refactoring Catalog](https://refactoring.com/catalog/)

---

## 요약

### 핵심 원칙

```yaml
1. 작은 단계로:
   - 한 번에 하나의 기법만
   - 자주 커밋
   - 자주 테스트

2. 안전하게:
   - 리팩토링 전 테스트 작성
   - 각 단계마다 테스트 실행
   - CI/CD 통과 확인

3. 체계적으로:
   - Task로 관리
   - 체크리스트 사용
   - 코드 리뷰 필수

4. 지속적으로:
   - 주기적 리팩토링
   - Technical Debt 관리
   - 자동화 도구 활용
```

### Claude Teams 활용

```yaml
Task 생성:
  - 명확한 목표
  - 구체적인 단계
  - 측정 가능한 성공 기준

역할 분담:
  - Refactoring Lead: 계획
  - Developer Agent: 실행
  - QA Agent: 검증
  - Reviewer: 승인

자동화:
  - Pre-commit hooks
  - CI/CD 통합
  - 코드 메트릭 측정
```

---

**작성일**: 2026-02-07
**버전**: 1.0
**다음 업데이트**: 리팩토링 Task 완료 후 사례 추가
