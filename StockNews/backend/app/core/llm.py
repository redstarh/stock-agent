"""AWS Bedrock Claude LLM 클라이언트."""

import logging
import re
from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_bedrock_client():
    """Bedrock Runtime 클라이언트 (싱글턴)."""
    session_kwargs = {}
    if settings.aws_profile:
        session_kwargs["profile_name"] = settings.aws_profile
    elif settings.aws_access_key_id and settings.aws_secret_access_key:
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    session_kwargs["region_name"] = settings.aws_region
    session = boto3.Session(**session_kwargs)
    boto_config = Config(
        connect_timeout=5,
        read_timeout=30,
        retries={"max_attempts": 1},
    )
    return session.client("bedrock-runtime", config=boto_config)


def call_llm(system_prompt: str, user_message: str, *, model_id: str = "") -> str:
    """Bedrock Claude 호출.

    Args:
        system_prompt: 시스템 프롬프트
        user_message: 사용자 메시지
        model_id: 사용할 모델 ID (빈 문자열이면 settings.bedrock_model_id 사용)

    Returns:
        LLM 응답 텍스트

    Raises:
        RuntimeError: Bedrock 호출 실패 시
    """
    client = get_bedrock_client()
    resolved_model = model_id or settings.bedrock_model_id

    try:
        response = client.converse(
            modelId=resolved_model,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_message}],
                }
            ],
            inferenceConfig={
                "temperature": 0,
                "maxTokens": 1024,
            },
        )

        output_message = response["output"]["message"]
        text = output_message["content"][0]["text"]
        # Strip markdown code fences (e.g. ```json ... ```)
        stripped = re.sub(r'^```(?:\w+)?\s*\n?', '', text.strip())
        stripped = re.sub(r'\n?```\s*$', '', stripped)
        return stripped.strip()

    except Exception as e:
        logger.error("Bedrock LLM call failed: %s", e)
        raise RuntimeError(f"Bedrock LLM call failed: {e}") from e
