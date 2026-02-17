"""
공통 테스트 픽스처
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# 프로젝트가 구현되면 실제 모듈로 교체
# from src.main import app
# from src.database import Base, get_db
# from src.auth.models import User
# from src.trading.models import Order, Position, Account


# ==================== Database Fixtures ====================

@pytest.fixture(scope="function")
def db_engine():
    """테스트용 DB 엔진"""
    engine = create_engine(
        "postgresql://test:test@localhost:5432/test_trading",
        echo=False
    )
    # Base.metadata.create_all(bind=engine)
    yield engine
    # Base.metadata.drop_all(bind=engine)
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
    # def override_get_db():
    #     try:
    #         yield db_session
    #     finally:
    #         pass

    # app.dependency_overrides[get_db] = override_get_db

    # with TestClient(app) as test_client:
    #     yield test_client

    # app.dependency_overrides.clear()
    pass


# ==================== User Fixtures ====================

@pytest.fixture
def test_user(db_session):
    """테스트 사용자"""
    # user = User(
    #     email="test@example.com",
    #     hashed_password="$2b$12$...",  # bcrypt hash
    #     is_active=True
    # )
    # db_session.add(user)
    # db_session.commit()
    # db_session.refresh(user)
    # return user
    pass


@pytest.fixture
def auth_headers(test_user):
    """인증 헤더"""
    # from src.auth.utils import create_access_token
    # token = create_access_token({"sub": test_user.email})
    # return {"Authorization": f"Bearer {token}"}
    pass


# ==================== Trading Fixtures ====================

@pytest.fixture
def test_account(db_session, test_user):
    """테스트 계좌"""
    # account = Account(
    #     user_id=test_user.id,
    #     account_type="simulator",
    #     balance=10000.0
    # )
    # db_session.add(account)
    # db_session.commit()
    # return account
    pass


@pytest.fixture
def test_order(db_session, test_account):
    """테스트 주문"""
    # order = Order(
    #     account_id=test_account.id,
    #     symbol="AAPL",
    #     side="buy",
    #     quantity=10,
    #     price=150.0,
    #     status="pending"
    # )
    # db_session.add(order)
    # db_session.commit()
    # return order
    pass


@pytest.fixture
def test_position(db_session, test_account):
    """테스트 포지션"""
    # position = Position(
    #     account_id=test_account.id,
    #     symbol="AAPL",
    #     quantity=10,
    #     avg_price=150.0
    # )
    # db_session.add(position)
    # db_session.commit()
    # return position
    pass
