"""Account API router unit tests"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app
import src.api.account as account_module


@pytest.fixture(autouse=True)
def reset_account_client():
    """Reset global _account_client before each test"""
    account_module._account_client = None
    yield
    account_module._account_client = None


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestGetAccountClient:
    """Test get_account_client singleton creation"""

    @patch("src.api.account.KiwoomAccount")
    @patch("src.api.account.KiwoomAuth")
    @patch("src.api.account.Settings")
    def test_get_account_client_creates_singleton(
        self, mock_settings_cls, mock_auth_cls, mock_account_cls
    ):
        """Test get_account_client creates client on first call"""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.KIWOOM_APP_KEY = "test_key"
        mock_settings.KIWOOM_APP_SECRET = "test_secret"
        mock_settings.KIWOOM_BASE_URL = "https://test.api.com"
        mock_settings_cls.return_value = mock_settings

        mock_auth = MagicMock()
        mock_auth_cls.return_value = mock_auth

        mock_account = MagicMock()
        mock_account_cls.return_value = mock_account

        # Call function
        result = account_module.get_account_client()

        # Verify Settings was instantiated
        mock_settings_cls.assert_called_once()

        # Verify KiwoomAuth was created with correct parameters
        mock_auth_cls.assert_called_once_with(
            app_key="test_key",
            app_secret="test_secret",
            base_url="https://test.api.com",
        )

        # Verify KiwoomAccount was created with auth and base_url
        mock_account_cls.assert_called_once_with(
            auth=mock_auth, base_url="https://test.api.com"
        )

        # Verify returned client is the mock account
        assert result is mock_account

        # Verify global variable was set
        assert account_module._account_client is mock_account

    @patch("src.api.account.KiwoomAccount")
    @patch("src.api.account.KiwoomAuth")
    @patch("src.api.account.Settings")
    def test_get_account_client_returns_cached(
        self, mock_settings_cls, mock_auth_cls, mock_account_cls
    ):
        """Test get_account_client returns same instance on subsequent calls"""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.KIWOOM_APP_KEY = "test_key"
        mock_settings.KIWOOM_APP_SECRET = "test_secret"
        mock_settings.KIWOOM_BASE_URL = "https://test.api.com"
        mock_settings_cls.return_value = mock_settings

        mock_auth = MagicMock()
        mock_auth_cls.return_value = mock_auth

        mock_account = MagicMock()
        mock_account_cls.return_value = mock_account

        # First call
        result1 = account_module.get_account_client()

        # Second call
        result2 = account_module.get_account_client()

        # Verify Settings was only called once (singleton behavior)
        assert mock_settings_cls.call_count == 1

        # Verify KiwoomAuth was only called once
        assert mock_auth_cls.call_count == 1

        # Verify KiwoomAccount was only called once
        assert mock_account_cls.call_count == 1

        # Verify both calls return the same instance
        assert result1 is result2
        assert result1 is mock_account


class TestBalanceEndpoint:
    """Test /api/v1/account/balance endpoint"""

    @patch("src.api.account.get_account_client")
    @pytest.mark.asyncio
    async def test_balance_endpoint(self, mock_get_client, client):
        """Test balance endpoint returns data from client"""
        # Setup mock client
        mock_account = MagicMock()
        mock_account.get_balance = AsyncMock(
            return_value={
                "account_number": "12345678",
                "total_balance": 10000000,
                "available_cash": 5000000,
                "total_pnl": 500000,
            }
        )
        mock_get_client.return_value = mock_account

        # Call endpoint
        response = client.get("/api/v1/account/balance")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["account_number"] == "12345678"
        assert data["total_balance"] == 10000000
        assert data["available_cash"] == 5000000
        assert data["total_pnl"] == 500000

        # Verify client method was called
        mock_account.get_balance.assert_called_once()


class TestPositionsEndpoint:
    """Test /api/v1/account/positions endpoint"""

    @patch("src.api.account.get_account_client")
    @pytest.mark.asyncio
    async def test_positions_endpoint(self, mock_get_client, client):
        """Test positions endpoint returns data from client"""
        # Setup mock client
        mock_account = MagicMock()
        mock_account.get_positions = AsyncMock(
            return_value=[
                {
                    "symbol": "005930",
                    "quantity": 100,
                    "avg_price": 70000,
                    "current_price": 75000,
                    "pnl": 500000,
                    "pnl_ratio": 7.14,
                },
                {
                    "symbol": "000660",
                    "quantity": 50,
                    "avg_price": 100000,
                    "current_price": 105000,
                    "pnl": 250000,
                    "pnl_ratio": 5.0,
                },
            ]
        )
        mock_get_client.return_value = mock_account

        # Call endpoint
        response = client.get("/api/v1/account/positions")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["symbol"] == "005930"
        assert data[0]["quantity"] == 100
        assert data[1]["symbol"] == "000660"
        assert data[1]["quantity"] == 50

        # Verify client method was called
        mock_account.get_positions.assert_called_once()


class TestPnlEndpoint:
    """Test /api/v1/account/pnl endpoint"""

    @patch("src.api.account.get_account_client")
    @pytest.mark.asyncio
    async def test_pnl_endpoint(self, mock_get_client, client):
        """Test pnl endpoint returns data from client"""
        # Setup mock client
        mock_account = MagicMock()
        mock_account.get_pnl = AsyncMock(
            return_value={
                "daily_pnl": 150000,
                "daily_pnl_ratio": 1.5,
                "total_pnl": 750000,
                "total_pnl_ratio": 7.5,
                "realized_pnl": 500000,
                "unrealized_pnl": 250000,
            }
        )
        mock_get_client.return_value = mock_account

        # Call endpoint
        response = client.get("/api/v1/account/pnl")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["daily_pnl"] == 150000
        assert data["daily_pnl_ratio"] == 1.5
        assert data["total_pnl"] == 750000
        assert data["realized_pnl"] == 500000
        assert data["unrealized_pnl"] == 250000

        # Verify client method was called
        mock_account.get_pnl.assert_called_once()
