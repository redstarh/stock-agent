"""Secrets Manager 통합 모듈.

환경 변수, AWS Secrets Manager, 파일 기반 시크릿 제공자를 지원합니다.
"""

import json
import os
from pathlib import Path
from typing import Any, Protocol


class SecretsProvider(Protocol):
    """시크릿 제공자 프로토콜."""

    def get_secret(self, key: str) -> str | None:
        """시크릿 값을 조회합니다.

        Args:
            key: 시크릿 키

        Returns:
            시크릿 값 또는 None (키가 없는 경우)
        """
        ...


class EnvSecretsProvider:
    """환경 변수 기반 시크릿 제공자 (기본 동작)."""

    def get_secret(self, key: str) -> str | None:
        """환경 변수에서 시크릿을 조회합니다.

        Args:
            key: 환경 변수 이름

        Returns:
            환경 변수 값 또는 None
        """
        return os.environ.get(key)


class FileSecretsProvider:
    """파일 기반 시크릿 제공자 (JSON 파일 또는 Docker secrets)."""

    def __init__(self, file_path: str) -> None:
        """파일 기반 시크릿 제공자를 초기화합니다.

        Args:
            file_path: JSON 파일 경로
        """
        self.file_path = Path(file_path)
        self._secrets: dict[str, Any] | None = None

    def _load_secrets(self) -> dict[str, Any]:
        """시크릿 파일을 로드합니다 (캐싱 포함)."""
        if self._secrets is None:
            if not self.file_path.exists():
                self._secrets = {}
            else:
                with open(self.file_path, encoding="utf-8") as f:
                    self._secrets = json.load(f)
        return self._secrets

    def get_secret(self, key: str) -> str | None:
        """JSON 파일에서 시크릿을 조회합니다.

        Args:
            key: 시크릿 키

        Returns:
            시크릿 값 또는 None
        """
        secrets = self._load_secrets()
        value = secrets.get(key)
        return str(value) if value is not None else None


class AWSSecretsManagerProvider:
    """AWS Secrets Manager 기반 시크릿 제공자."""

    def __init__(self, secret_name: str, region_name: str = "") -> None:
        """AWS Secrets Manager 제공자를 초기화합니다.

        Args:
            secret_name: AWS Secrets Manager 시크릿 이름
            region_name: AWS 리전 (선택 사항)

        Raises:
            ImportError: boto3가 설치되지 않은 경우
        """
        try:
            import boto3
        except ImportError as e:
            raise ImportError(
                "boto3가 설치되지 않았습니다. 'pip install boto3'로 설치하세요."
            ) from e

        self.secret_name = secret_name
        self.region_name = region_name or "us-east-1"
        self._client = boto3.client("secretsmanager", region_name=self.region_name)
        self._secrets: dict[str, Any] | None = None

    def _fetch_secrets(self) -> dict[str, Any]:
        """AWS Secrets Manager에서 시크릿을 가져옵니다 (캐싱 포함)."""
        if self._secrets is None:
            try:
                response = self._client.get_secret_value(SecretId=self.secret_name)
                secret_string = response.get("SecretString", "{}")
                self._secrets = json.loads(secret_string)
            except Exception as e:
                # 실패 시 빈 딕셔너리 반환 (graceful degradation)
                print(f"AWS Secrets Manager 조회 실패: {e}")
                self._secrets = {}
        return self._secrets

    def get_secret(self, key: str) -> str | None:
        """AWS Secrets Manager에서 시크릿을 조회합니다.

        Args:
            key: 시크릿 키

        Returns:
            시크릿 값 또는 None
        """
        secrets = self._fetch_secrets()
        value = secrets.get(key)
        return str(value) if value is not None else None


def create_secrets_provider(provider_type: str, **kwargs: Any) -> SecretsProvider:
    """시크릿 제공자를 생성합니다.

    Args:
        provider_type: 제공자 타입 ("", "env", "aws", "file")
        **kwargs: 제공자별 추가 인자
            - aws: secret_name (필수), region_name (선택)
            - file: file_path (필수)

    Returns:
        SecretsProvider 인스턴스

    Raises:
        ValueError: 알 수 없는 provider_type인 경우
    """
    provider_type = provider_type.lower().strip()

    if provider_type in ("", "env"):
        return EnvSecretsProvider()
    elif provider_type == "aws":
        secret_name = kwargs.get("secret_name")
        if not secret_name:
            raise ValueError("AWS provider requires 'secret_name' argument")
        region_name = kwargs.get("region_name", "")
        return AWSSecretsManagerProvider(secret_name, region_name)
    elif provider_type == "file":
        file_path = kwargs.get("file_path")
        if not file_path:
            raise ValueError("File provider requires 'file_path' argument")
        return FileSecretsProvider(file_path)
    else:
        raise ValueError(f"Unknown secrets provider type: {provider_type}")
