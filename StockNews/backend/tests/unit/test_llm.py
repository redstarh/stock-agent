"""Bedrock LLM 클라이언트 테스트."""

import json
import pytest
from unittest.mock import MagicMock, patch


class TestCallLlm:
    """call_llm() 함수 테스트."""

    def test_call_llm_returns_text(self, monkeypatch):
        """정상 호출 시 응답 텍스트 반환."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": '{"result": "ok"}'}]
                }
            }
        }
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)

        from app.core.llm import call_llm
        result = call_llm("system prompt", "user message")

        assert result == '{"result": "ok"}'
        mock_client.converse.assert_called_once()

        # Verify correct parameters passed
        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["system"] == [{"text": "system prompt"}]
        assert call_kwargs["messages"][0]["role"] == "user"
        assert call_kwargs["messages"][0]["content"][0]["text"] == "user message"
        assert call_kwargs["inferenceConfig"]["temperature"] == 0

    def test_call_llm_json_response(self, monkeypatch):
        """JSON 응답을 올바르게 반환."""
        expected = {"sentiment": "positive", "score": 0.85, "confidence": 0.95}
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(expected)}]
                }
            }
        }
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)

        from app.core.llm import call_llm
        result = call_llm("analyze", "test text")
        parsed = json.loads(result)

        assert parsed == expected

    def test_call_llm_raises_on_error(self, monkeypatch):
        """Bedrock 호출 실패 시 RuntimeError."""
        mock_client = MagicMock()
        mock_client.converse.side_effect = Exception("Connection refused")
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)

        from app.core.llm import call_llm
        with pytest.raises(RuntimeError, match="Bedrock LLM call failed"):
            call_llm("system", "user")

    def test_call_llm_uses_model_from_settings(self, monkeypatch):
        """settings.bedrock_model_id를 사용."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "ok"}]}}
        }
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)
        monkeypatch.setattr("app.core.llm.settings.bedrock_model_id", "test-model-id")

        from app.core.llm import call_llm
        call_llm("sys", "usr")

        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["modelId"] == "test-model-id"

    def test_call_llm_custom_model_id(self, monkeypatch):
        """model_id 파라미터로 모델 지정."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "ok"}]}}
        }
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)

        from app.core.llm import call_llm
        call_llm("sys", "usr", model_id="custom-model")

        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["modelId"] == "custom-model"

    def test_call_llm_strips_code_fences(self, monkeypatch):
        """마크다운 코드펜스를 제거."""
        mock_client = MagicMock()
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": '```json\n{"sentiment": "positive"}\n```'}]}}
        }
        monkeypatch.setattr("app.core.llm.get_bedrock_client", lambda: mock_client)

        from app.core.llm import call_llm
        result = call_llm("sys", "usr")

        assert result == '{"sentiment": "positive"}'


class TestGetBedrockClient:
    """get_bedrock_client() 테스트."""

    def test_creates_client_with_credentials(self, monkeypatch):
        """AWS credentials가 있으면 전달."""
        monkeypatch.setattr("app.core.llm.settings.aws_profile", "")
        monkeypatch.setattr("app.core.llm.settings.aws_access_key_id", "test-key")
        monkeypatch.setattr("app.core.llm.settings.aws_secret_access_key", "test-secret")
        monkeypatch.setattr("app.core.llm.settings.aws_region", "ap-northeast-2")

        mock_session = MagicMock()
        mock_session_cls = MagicMock(return_value=mock_session)
        monkeypatch.setattr("app.core.llm.boto3.Session", mock_session_cls)

        from app.core.llm import get_bedrock_client
        get_bedrock_client.cache_clear()

        get_bedrock_client()

        mock_session_cls.assert_called_once_with(
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="ap-northeast-2",
        )
        mock_session.client.assert_called_once_with("bedrock-runtime")
        get_bedrock_client.cache_clear()

    def test_creates_client_with_profile(self, monkeypatch):
        """AWS profile이 있으면 profile_name 사용."""
        monkeypatch.setattr("app.core.llm.settings.aws_profile", "my-profile")
        monkeypatch.setattr("app.core.llm.settings.aws_access_key_id", "")
        monkeypatch.setattr("app.core.llm.settings.aws_secret_access_key", "")
        monkeypatch.setattr("app.core.llm.settings.aws_region", "us-east-1")

        mock_session = MagicMock()
        mock_session_cls = MagicMock(return_value=mock_session)
        monkeypatch.setattr("app.core.llm.boto3.Session", mock_session_cls)

        from app.core.llm import get_bedrock_client
        get_bedrock_client.cache_clear()

        get_bedrock_client()

        mock_session_cls.assert_called_once_with(
            profile_name="my-profile",
            region_name="us-east-1",
        )
        mock_session.client.assert_called_once_with("bedrock-runtime")
        get_bedrock_client.cache_clear()

    def test_creates_client_without_credentials(self, monkeypatch):
        """AWS credentials가 없으면 기본 credential chain 사용."""
        monkeypatch.setattr("app.core.llm.settings.aws_profile", "")
        monkeypatch.setattr("app.core.llm.settings.aws_access_key_id", "")
        monkeypatch.setattr("app.core.llm.settings.aws_secret_access_key", "")
        monkeypatch.setattr("app.core.llm.settings.aws_region", "us-east-1")

        mock_session = MagicMock()
        mock_session_cls = MagicMock(return_value=mock_session)
        monkeypatch.setattr("app.core.llm.boto3.Session", mock_session_cls)

        from app.core.llm import get_bedrock_client
        get_bedrock_client.cache_clear()

        get_bedrock_client()

        mock_session_cls.assert_called_once_with(
            region_name="us-east-1",
        )
        mock_session.client.assert_called_once_with("bedrock-runtime")
        get_bedrock_client.cache_clear()
