"""Anthropic Claude API 클라이언트

Claude 3.5 Haiku를 사용하여 실제 LLM 호출을 수행합니다.
가장 저렴한 모델로 라우팅 분류 + 각 스텝 실행에 사용합니다.

사용 모델: claude-3-5-haiku-20241022
- Input: $0.80 / 1M tokens
- Output: $4.00 / 1M tokens
"""

import httpx
import time
from typing import Optional

from .base_client import BaseLLMClient, LLMResponse


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-haiku-latest"


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic Claude API 클라이언트"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model
        self._client = httpx.Client(timeout=60.0)

    def generate(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Claude API를 호출합니다.

        model_id는 라우팅 엔진이 추천한 모델명이지만,
        실제로는 모두 claude-3-5-haiku로 호출합니다.
        (시뮬레이션: 추천 모델이 실제로 응답한다고 가정)
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # 시스템 프롬프트에 추천 모델 역할을 부여
        sys_prompt = system_prompt or ""
        sys_prompt += f"\n\n[시뮬레이션] 너는 지금 '{model_id}' 모델 역할을 하고 있어. 간결하고 효율적으로 답변해."

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        }

        if sys_prompt.strip():
            body["system"] = sys_prompt.strip()

        start = time.time()

        try:
            response = self._client.post(
                ANTHROPIC_API_URL,
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            data = response.json()

            elapsed = (time.time() - start) * 1000

            # 응답 파싱
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            return LLMResponse(
                model_id=model_id,
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                latency_ms=round(elapsed, 2),
                is_mock=False,
            )

        except httpx.HTTPStatusError as e:
            return LLMResponse(
                model_id=model_id,
                content=f"[API 오류] {e.response.status_code}: {e.response.text[:200]}",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=0,
                is_mock=True,
            )
        except Exception as e:
            return LLMResponse(
                model_id=model_id,
                content=f"[연결 오류] {str(e)}",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                latency_ms=0,
                is_mock=True,
            )

    def is_available(self) -> bool:
        """API 키가 설정되어 있으면 사용 가능"""
        return bool(self.api_key)
