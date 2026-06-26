"""Google Gemini API 클라이언트

Gemini 2.0 Flash를 사용하여 실제 LLM 호출을 수행합니다.
무료 tier: 분당 15회, 일 1500회.

사용 모델: gemini-2.0-flash
"""

import httpx
import time
from typing import Optional

from .base_client import BaseLLMClient, LLMResponse


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini API 클라이언트"""

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
        """Gemini API 호출"""

        url = f"{GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"

        # 시스템 프롬프트 + 유저 프롬프트 조합
        full_prompt = ""
        if system_prompt:
            full_prompt = system_prompt + "\n\n"
        full_prompt += prompt

        body = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }

        start = time.time()

        try:
            response = self._client.post(url, json=body)
            response.raise_for_status()
            data = response.json()

            elapsed = (time.time() - start) * 1000

            # 응답 파싱
            content = ""
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    content += part.get("text", "")

            # 토큰 사용량
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

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
        return bool(self.api_key)
