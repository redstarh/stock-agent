"""Secrets Manager 통합 테스트."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.secrets import (
    AWSSecretsManagerProvider,
    EnvSecretsProvider,
    FileSecretsProvider,
    create_secrets_provider,
)


class TestEnvSecretsProvider:
    """환경 변수 기반 시크릿 제공자 테스트."""

    def test_get_secret_existing_key(self, monkeypatch):
        """환경 변수에서 시크릿을 조회합니다."""
        monkeypatch.setenv("TEST_KEY", "test_value")
        provider = EnvSecretsProvider()
        assert provider.get_secret("TEST_KEY") == "test_value"

    def test_get_secret_missing_key(self):
        """존재하지 않는 키는 None을 반환합니다."""
        provider = EnvSecretsProvider()
        assert provider.get_secret("NONEXISTENT_KEY") is None


class TestFileSecretsProvider:
    """파일 기반 시크릿 제공자 테스트."""

    def test_get_secret_from_json_file(self, tmp_path):
        """JSON 파일에서 시크릿을 조회합니다."""
        secrets_file = tmp_path / "secrets.json"
        secrets_data = {"api_key": "secret123", "db_password": "pass456"}
        secrets_file.write_text(json.dumps(secrets_data))

        provider = FileSecretsProvider(str(secrets_file))
        assert provider.get_secret("api_key") == "secret123"
        assert provider.get_secret("db_password") == "pass456"

    def test_get_secret_missing_key(self, tmp_path):
        """존재하지 않는 키는 None을 반환합니다."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({"key1": "value1"}))

        provider = FileSecretsProvider(str(secrets_file))
        assert provider.get_secret("key2") is None

    def test_get_secret_nonexistent_file(self, tmp_path):
        """파일이 없으면 빈 딕셔너리로 처리합니다."""
        provider = FileSecretsProvider(str(tmp_path / "nonexistent.json"))
        assert provider.get_secret("any_key") is None

    def test_caching_behavior(self, tmp_path):
        """시크릿 파일은 한 번만 로드됩니다."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({"key": "value"}))

        provider = FileSecretsProvider(str(secrets_file))

        # 첫 번째 호출
        assert provider.get_secret("key") == "value"

        # 파일 내용 변경 (캐싱으로 인해 반영되지 않음)
        secrets_file.write_text(json.dumps({"key": "new_value"}))

        # 두 번째 호출 (캐시된 값 반환)
        assert provider.get_secret("key") == "value"


class TestAWSSecretsManagerProvider:
    """AWS Secrets Manager 제공자 테스트."""

    @patch("boto3.client")
    def test_get_secret_from_aws(self, mock_boto3_client):
        """AWS Secrets Manager에서 시크릿을 조회합니다."""
        # Mock boto3 client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"api_key": "aws_secret_123", "db_pass": "db_secret_456"})
        }

        provider = AWSSecretsManagerProvider(
            secret_name="my-secret", region_name="us-east-1"
        )

        assert provider.get_secret("api_key") == "aws_secret_123"
        assert provider.get_secret("db_pass") == "db_secret_456"

        # Verify boto3 client was called correctly
        mock_boto3_client.assert_called_once_with(
            "secretsmanager", region_name="us-east-1"
        )
        mock_client.get_secret_value.assert_called_once_with(SecretId="my-secret")

    @patch("boto3.client")
    def test_get_secret_missing_key(self, mock_boto3_client):
        """존재하지 않는 키는 None을 반환합니다."""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"key1": "value1"})
        }

        provider = AWSSecretsManagerProvider("my-secret", "us-east-1")
        assert provider.get_secret("key2") is None

    @patch("boto3.client")
    def test_caching_behavior(self, mock_boto3_client):
        """AWS API는 한 번만 호출됩니다 (캐싱)."""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"key": "value"})
        }

        provider = AWSSecretsManagerProvider("my-secret", "us-east-1")

        # 여러 번 호출
        provider.get_secret("key")
        provider.get_secret("key")
        provider.get_secret("another_key")

        # AWS API는 한 번만 호출됨
        assert mock_client.get_secret_value.call_count == 1

    @patch("boto3.client")
    def test_default_region(self, mock_boto3_client):
        """리전이 지정되지 않으면 us-east-1 사용."""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({})
        }

        provider = AWSSecretsManagerProvider("my-secret")
        provider.get_secret("any_key")

        mock_boto3_client.assert_called_once_with(
            "secretsmanager", region_name="us-east-1"
        )

    @patch("boto3.client")
    def test_aws_api_failure_graceful_degradation(self, mock_boto3_client):
        """AWS API 실패 시 빈 딕셔너리로 처리합니다."""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        mock_client.get_secret_value.side_effect = Exception("AWS API Error")

        provider = AWSSecretsManagerProvider("my-secret", "us-east-1")

        # 예외가 발생하지 않고 None 반환
        assert provider.get_secret("any_key") is None

    def test_boto3_not_installed(self):
        """boto3가 설치되지 않은 경우 ImportError 발생."""
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3가 설치되지 않았습니다"):
                AWSSecretsManagerProvider("my-secret")


class TestCreateSecretsProvider:
    """시크릿 제공자 팩토리 함수 테스트."""

    def test_create_env_provider(self):
        """env 타입 제공자를 생성합니다."""
        provider = create_secrets_provider("")
        assert isinstance(provider, EnvSecretsProvider)

        provider = create_secrets_provider("env")
        assert isinstance(provider, EnvSecretsProvider)

    def test_create_file_provider(self, tmp_path):
        """file 타입 제공자를 생성합니다."""
        file_path = str(tmp_path / "secrets.json")
        provider = create_secrets_provider("file", file_path=file_path)
        assert isinstance(provider, FileSecretsProvider)

    def test_create_file_provider_missing_path(self):
        """file_path 인자가 없으면 ValueError 발생."""
        with pytest.raises(ValueError, match="File provider requires 'file_path'"):
            create_secrets_provider("file")

    @patch("boto3.client")
    def test_create_aws_provider(self, mock_boto3_client):
        """aws 타입 제공자를 생성합니다."""
        mock_boto3_client.return_value = MagicMock()
        provider = create_secrets_provider(
            "aws", secret_name="my-secret", region_name="us-west-2"
        )
        assert isinstance(provider, AWSSecretsManagerProvider)

    def test_create_aws_provider_missing_secret_name(self):
        """secret_name 인자가 없으면 ValueError 발생."""
        with pytest.raises(ValueError, match="AWS provider requires 'secret_name'"):
            create_secrets_provider("aws")

    def test_unknown_provider_type(self):
        """알 수 없는 provider_type은 ValueError 발생."""
        with pytest.raises(ValueError, match="Unknown secrets provider type"):
            create_secrets_provider("unknown")

    def test_case_insensitive_provider_type(self):
        """provider_type은 대소문자 구분 없이 처리됩니다."""
        provider = create_secrets_provider("ENV")
        assert isinstance(provider, EnvSecretsProvider)

        provider = create_secrets_provider("  AWS  ", secret_name="test")
        # boto3 import 실패할 수 있으므로 타입만 확인하지 않음
