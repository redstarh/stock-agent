"""AWS Bedrock Claude LLM 클라이언트."""

import json
import logging
from functools import lru_cache

import boto3

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_bedrock_client():
    """Bedrock Runtime 클라이언트 (싱글턴)."""
    kwargs = {
        "service_name": "bedrock-runtime",
        "region_name": settings.aws_region,
    }
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    return boto3.client(**kwargs)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Bedrock Claude 호출.

    Args:
        system_prompt: 시스템 프롬프트
        user_message: 사용자 메시지

    Returns:
        LLM 응답 텍스트

    Raises:
        RuntimeError: Bedrock 호출 실패 시
    """
    client = get_bedrock_client()

    try:
        response = client.converse(
            modelId=settings.bedrock_model_id,
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
        return output_message["content"][0]["text"]

    except Exception as e:
        logger.error("Bedrock LLM call failed: %s", e)
        raise RuntimeError(f"Bedrock LLM call failed: {e}") from e
