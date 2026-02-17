# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Stock Trading System - A dual-mode trading platform supporting both simulated and live trading with Korean brokerage integration. This is a **Modular Monolith** architecture optimized for individual/small team development.

**Status**: Early development stage 🚧
**Tech Stack**: Python FastAPI (Backend) + React 18 TypeScript (Frontend)
**Target Coverage**: 80%+

## Architecture

### Modular Monolith (3 Services)

```
StockAgent/
├── src/backend/          # FastAPI backend (modular monolith)
│   ├── auth/             # Authentication & authorization
│   ├── trading/          # Order processing & execution
│   ├── portfolio/        # Portfolio management
│   ├── risk/             # Risk management
│   └── analytics/        # Analysis & statistics
├── src/frontend/         # React + TypeScript frontend
└── docs/                 # Project documentation
```

**Future Services** (not yet implemented):
- Market Data Service: Real-time WebSocket price feeds
- Broker Connector: Korean brokerage API integration

### Key Design Decisions

1. **Modular Monolith over Microservices**: Simplified deployment, easier development, 90% cost reduction ($2000/mo → $20/mo)
2. **TDD-First**: Write tests before implementation (Red-Green-Refactor cycle)
3. **SOLID Principles**: Single Responsibility, Dependency Injection throughout
4. **Dual-Mode Trading**: Single codebase handles both simulator and live trading via Trading Abstraction Layer

## Development Commands

### Backend (Python/FastAPI)

```bash
cd StockAgent/src/backend

# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../../requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v                           # All tests
pytest tests/unit/ -v                      # Unit tests only
pytest tests/integration/ -v               # Integration tests only
pytest tests/ -v --cov=src --cov-report=html  # With coverage

# Run specific test file
pytest tests/unit/test_order_model.py -v

# Run specific test function
pytest tests/unit/test_order_model.py::TestOrderModel::test_create_order -v

# Code quality
black src/ tests/                          # Format code
flake8 src/ tests/                         # Lint
mypy src/                                  # Type check
isort src/ tests/                          # Sort imports

# Check test coverage
pytest --cov=src --cov-report=term-missing
open htmlcov/index.html  # View detailed coverage report
```

### Frontend (React/TypeScript)

```bash
cd StockAgent/src/frontend

# Setup
npm install

# Development
npm run dev                # Start dev server

# Testing
npm test                   # Run tests in watch mode
npm test -- --coverage     # Run with coverage
npm test -- --watchAll=false  # Run once (CI mode)

# Run specific test file
npm test OrderForm.test.tsx

# Code quality
npm run lint               # ESLint
npm run type-check         # TypeScript check
npm run format             # Prettier format
```

### Jira Import (Project Management)

```bash
# Setup environment
cp .env.example .env
# Edit .env with your Jira credentials

# Import stories/tasks to Jira
cd StockAgent/src
python jira_import.py      # Import from docs/jira-import.csv

# Create sprints
python jira_sprints.py     # Create 5 sprint structure
```

## Test-Driven Development (TDD)

**CRITICAL**: This project follows strict TDD. Always write tests BEFORE implementation.

### TDD Workflow (Red-Green-Refactor)

```bash
# 1. RED: Write failing test
vim tests/unit/test_portfolio_service.py
pytest tests/unit/test_portfolio_service.py  # Should FAIL

# 2. GREEN: Implement minimum code to pass
vim src/portfolio/service.py
pytest tests/unit/test_portfolio_service.py  # Should PASS

# 3. REFACTOR: Improve code quality
# Refactor while keeping tests green
pytest tests/  # All tests still pass
```

### Test Structure

```python
# Unit Test Example (tests/unit/test_order_service.py)
def test_create_order_success():
    """Given-When-Then pattern"""
    # Given: Setup test data
    order_data = OrderRequest(symbol="AAPL", quantity=10, price=150.0)

    # When: Execute action
    order = order_service.create_order(order_data)

    # Then: Verify result
    assert order.symbol == "AAPL"
    assert order.status == OrderStatus.PENDING
```

### Coverage Requirements

- **Overall**: 80% minimum
- **Business Logic**: 90% minimum (trading, portfolio, risk modules)
- **API Endpoints**: 85% minimum

## Code Organization Principles

### SOLID Principles (Enforced)

1. **Single Responsibility**: Each class has ONE reason to change
   - Good: `OrderValidator`, `OrderCalculator`, `OrderRepository`
   - Bad: `OrderService` doing validation + calculation + saving + notification

2. **Dependency Injection**: Always inject dependencies via constructor
   ```python
   # Good
   class OrderService:
       def __init__(self, repository: OrderRepository,
                    validator: OrderValidator):
           self.repository = repository
           self.validator = validator

   # Bad
   class OrderService:
       def __init__(self):
           self.repository = PostgreSQLRepository()  # Hard-coded dependency
   ```

3. **Small Methods**: Keep methods under 15 lines (ideally 10)
4. **No Magic Numbers**: Extract all constants to named variables
   ```python
   # Good
   COMMISSION_RATE = Decimal("0.001")  # 0.1%
   commission = amount * COMMISSION_RATE

   # Bad
   commission = amount * 0.001  # What is 0.001?
   ```

### File Organization Patterns

```
backend/src/module_name/
├── models.py        # SQLAlchemy models (entities)
├── schemas.py       # Pydantic schemas (DTOs)
├── service.py       # Business logic
├── repository.py    # Database operations
├── router.py        # FastAPI endpoints
└── exceptions.py    # Custom exceptions
```

## Common Development Tasks

### Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/portfolio-api

# 2. Write tests FIRST (TDD)
vim tests/unit/test_portfolio_service.py
vim tests/integration/test_api_portfolio.py
pytest tests/ -v  # Tests should FAIL

# 3. Implement feature
vim src/portfolio/service.py
vim src/portfolio/router.py
pytest tests/ -v  # Tests should PASS

# 4. Check coverage
pytest --cov=src --cov-report=html
# Ensure 80%+ coverage

# 5. Run code quality checks
black src/ tests/
flake8 src/ tests/
mypy src/

# 6. Commit (tests + implementation together)
git add .
git commit -m "feat: add portfolio calculation API

- Implement portfolio value calculation
- Add unrealized P&L tracking
- Tests: 95% coverage

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Refactoring Existing Code

**See**: `docs/REFACTORING.md` for comprehensive refactoring strategies

**Key Guidelines**:
- Never refactor without test coverage first
- Apply ONE refactoring technique at a time
- Run tests after each small change
- Commit frequently during refactoring

```bash
# 1. Ensure tests exist and pass
pytest tests/ -v

# 2. Apply refactoring technique (e.g., Extract Method)
# Keep tests green throughout

# 3. Verify tests still pass
pytest tests/ -v

# 4. Commit with descriptive message
git commit -m "refactor: extract method from OrderService.process_order"
```

### Fixing a Bug

```bash
# 1. Write a failing test that reproduces the bug
vim tests/unit/test_order_bug.py
pytest tests/unit/test_order_bug.py  # Should FAIL

# 2. Fix the bug
vim src/trading/service.py

# 3. Verify test passes
pytest tests/unit/test_order_bug.py  # Should PASS

# 4. Run all tests (regression check)
pytest tests/ -v

# 5. Commit
git commit -m "fix: handle negative quantity in order validation"
```

## Database & Testing

### Test Database Setup

```python
# tests/conftest.py defines shared fixtures
@pytest.fixture
def db_session():
    """Isolated test database session"""
    # Creates fresh test DB for each test
    # Automatically rolls back after test

@pytest.fixture
def test_user(db_session):
    """Pre-configured test user"""

@pytest.fixture
def test_account(db_session, test_user):
    """Test account with $10,000 balance"""
```

### Using Fixtures in Tests

```python
def test_create_order(test_account, db_session):
    """Use fixtures for test data"""
    order = Order(
        account_id=test_account.id,
        symbol="AAPL",
        quantity=10,
        price=150.0
    )
    db_session.add(order)
    db_session.commit()

    assert order.id is not None
```

## API Development Guidelines

### Endpoint Structure

```python
# router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("", status_code=201, response_model=OrderResponse)
def create_order(
    request: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Order:
    """
    Create a new order

    Args:
        request: Order details (symbol, quantity, price, side)
        db: Database session
        current_user: Authenticated user

    Returns:
        Created order with status "pending"

    Raises:
        HTTPException 400: Insufficient balance
        HTTPException 404: Account not found
    """
    service = OrderService(db)
    return service.create_order(request)
```

### Error Handling

```python
# Custom exceptions (exceptions.py)
class InsufficientBalanceError(Exception):
    """Raised when account balance is insufficient"""

# Service layer
def create_order(self, request: OrderRequest) -> Order:
    if account.balance < required:
        raise InsufficientBalanceError(
            f"Required: {required}, Available: {account.balance}"
        )

# Router layer
@router.post("")
def create_order(request: OrderRequest):
    try:
        return service.create_order(request)
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## CI/CD Integration

Tests run automatically on GitHub Actions for:
- `push` to `main` or `develop`
- Pull requests to `main` or `develop`

### Workflow Jobs

1. **backend-tests**: Python unit + integration tests with PostgreSQL + Redis
2. **frontend-tests**: Jest + React Testing Library
3. **lint**: Code quality checks (Black, Flake8, Mypy)

**Local pre-push check**:
```bash
# Run what CI will run
pytest tests/ -v --cov=src --cov-fail-under=80
black --check src/ tests/
flake8 src/ tests/
mypy src/
```

## Important Project Context

### Business Domain Knowledge

**Trading Modes**:
- **Simulator**: Virtual money, instant execution, no brokerage fees
- **Live Trading**: Real Korean brokerage integration (Kiwoom, eBest planned)

**Risk Management**:
- Daily loss limits
- Position size limits (max 30% of portfolio per position)
- Order value limits

**Commission Structure**:
```python
COMMISSION_RATE = Decimal("0.001")  # 0.1%
TAX_RATE = Decimal("0.003")         # 0.3% (sell only)
```

### Critical Business Logic

**Order Execution Flow**:
1. Validate order data (symbol, quantity, price, side)
2. Validate account status (active, sufficient balance)
3. Check risk limits (daily loss, position size)
4. Create order entity (status: PENDING)
5. Execute order (update balance, create/update position)
6. Update order status (status: FILLED)
7. Send notification

**Portfolio Calculation**:
- Current Value = ∑(quantity × current_price)
- Unrealized P&L = Current Value - Cost Basis
- ROI = (Current Value - Cost Basis) / Cost Basis × 100

## Documentation References

**Key Documents** (in `docs/`):
- `README.md`: Project overview, quick start, roadmap
- `TDD.md`: Comprehensive TDD guide with examples
- `REFACTORING.md`: Refactoring strategies and SOLID principles
- `project-workflow.md`: Design decision flow charts
- `personal-trading-system-architecture.md`: Detailed architecture

## Development Philosophy

### What We Value

1. **Tests First**: No implementation without tests
2. **Small Commits**: Commit frequently with clear messages
3. **SOLID Code**: Prefer multiple small classes over large ones
4. **Type Safety**: Use type hints everywhere (Python), strict mode (TypeScript)
5. **Explicit over Implicit**: Clear naming, no magic, well-documented

### What to Avoid

- ❌ Skipping tests "just this once"
- ❌ Magic numbers (0.001, 1000, etc.)
- ❌ Methods longer than 15 lines
- ❌ Classes with multiple responsibilities
- ❌ Hard-coded dependencies
- ❌ Committing directly to main
- ❌ Changing code behavior while refactoring

## Quick Reference

### Test Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.slow           # Slow-running test
@pytest.mark.auth           # Authentication tests
```

Run specific marker: `pytest -m unit`

### Common Patterns

**Repository Pattern**:
```python
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> Order: pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Optional[Order]: pass
```

**Service Pattern**:
```python
class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def create_order(self, request: OrderRequest) -> Order:
        # Business logic here
        return self.repository.save(order)
```

**Strategy Pattern** (for commission calculation):
```python
class CommissionStrategy(ABC):
    @abstractmethod
    def calculate(self, order: Order) -> Decimal: pass

class BasicCommission(CommissionStrategy):
    def calculate(self, order: Order) -> Decimal:
        return order.total * COMMISSION_RATE
```

## Getting Help

- Check documentation in `docs/` directory first
- Review test examples in `tests/unit/` and `tests/integration/`
- Jira Board: https://stockagent.atlassian.net/jira/software/projects/SCRUM/boards/1
- Project is in active development - expect frequent changes

---

**Last Updated**: 2026-02-10
**Project Version**: 1.0.0
**Phase**: MVP Development (Phase 1 of 4)
