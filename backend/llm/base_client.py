"""LLM 클라이언트 추상 인터페이스

모든 LLM 클라이언트는 이 인터페이스를 구현합니다.
모델 추천 엔진(router/)과 모델 호출부(llm/)를 분리하기 위한 레이어입니다.

사용법:
    client = AnthropicLLMClient(api_key=...)
    response = client.generate(model_id="claude-haiku", prompt="안녕")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """LLM 호출 결과"""
    model_id: str
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    is_mock: bool = False


class BaseLLMClient(ABC):
    """LLM 클라이언트 추상 베이스 클래스"""

    @abstractmethod
    def generate(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        모델 호출.

        Args:
            model_id: 호출할 모델 ID (model_catalog의 키)
            prompt: 사용자 프롬프트
            system_prompt: 시스템 프롬프트 (선택)
            max_tokens: 최대 출력 토큰
            temperature: 온도

        Returns:
            LLMResponse
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """클라이언트 사용 가능 여부"""
        ...
