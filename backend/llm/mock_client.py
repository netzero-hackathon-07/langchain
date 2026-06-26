"""Mock LLM 클라이언트

실제 API 호출 없이 모델 라우팅 로직을 테스트하기 위한 mock 클라이언트입니다.
선택된 모델에 따라 적절한 mock 응답을 생성합니다.
"""

import time
import random
from typing import Optional

from .base_client import BaseLLMClient, LLMResponse


# 모델별 mock 응답 템플릿
MOCK_RESPONSES = {
    "gemini-flash": "[Gemini Flash 응답] 빠르고 간결한 답변을 제공합니다. 요청하신 내용을 처리했습니다.",
    "gpt-4o-mini": "[GPT-4o Mini 응답] 범용적이고 효율적인 답변입니다. 요청을 분석하여 최적의 결과를 제공합니다.",
    "claude-haiku": "[Claude Haiku 응답] 간결하고 정확한 처리 결과입니다.",
    "gpt-4o": "[GPT-4o 응답] 심층적인 분석과 함께 고품질 답변을 제공합니다. 여러 관점에서 검토하였습니다.",
    "gemini-pro": "[Gemini Pro 응답] 균형 잡힌 분석과 함께 상세한 답변을 드립니다.",
    "claude-sonnet": "[Claude Sonnet 응답] 복잡한 추론과 정밀한 분석을 포함한 상세 답변입니다. 맥락을 고려하여 포괄적으로 설명드리겠습니다.",
    "claude-opus": "[Claude Opus 응답] 최고 수준의 추론과 분석을 제공합니다. 다각도의 관점에서 심층적으로 검토한 결과입니다.",
    "gemma-4-e2b": "[Gemma 4 E2B 응답] 경량 모델의 빠른 응답입니다.",
    "gemma-4-27b-a4b": "[Gemma 4 27B 응답] 오픈소스 모델의 효율적인 답변입니다.",
}

# 모델별 가상 응답 시간 (ms)
MOCK_LATENCY = {
    "gemini-flash": (50, 150),
    "gpt-4o-mini": (100, 300),
    "claude-haiku": (80, 200),
    "gpt-4o": (300, 800),
    "gemini-pro": (200, 500),
    "claude-sonnet": (400, 1000),
    "claude-opus": (800, 2000),
    "gemma-4-e2b": (30, 100),
    "gemma-4-27b-a4b": (80, 250),
}


class MockLLMClient(BaseLLMClient):
    """Mock LLM 클라이언트 - 테스트/개발용"""

    def generate(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Mock 응답을 생성합니다.
        실제 LLM 호출 대신 모델별 템플릿 응답을 반환합니다.
        """
        # 가상 지연 시간
        latency_range = MOCK_LATENCY.get(model_id, (100, 500))
        latency_ms = random.uniform(*latency_range)

        # 토큰 추정
        input_tokens = max(len(prompt) * 2, 20)
        output_tokens = random.randint(80, min(max_tokens, 500))
        total_tokens = input_tokens + output_tokens

        # Mock 응답 생성
        base_response = MOCK_RESPONSES.get(
            model_id,
            f"[{model_id} 응답] 요청을 처리했습니다."
        )
        content = f"{base_response}\n\n(원본 요청: {prompt[:100]}{'...' if len(prompt) > 100 else ''})"

        return LLMResponse(
            model_id=model_id,
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            is_mock=True,
        )

    def is_available(self) -> bool:
        return True
