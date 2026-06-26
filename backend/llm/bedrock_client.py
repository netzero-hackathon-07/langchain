"""Amazon Bedrock LLM 클라이언트 (Skeleton)

현재 학교 AWS 계정에서 Bedrock API 키 생성 권한이 막혀 있으므로,
이 파일은 구조만 정의합니다.

나중에 권한이 풀리면:
1. boto3 또는 langchain-aws 의존성 추가
2. 아래 TODO 부분을 구현
3. main.py에서 MockLLMClient를 BedrockLLMClient로 교체

교체 방법:
    # main.py
    from llm.bedrock_client import BedrockLLMClient
    llm_client = BedrockLLMClient(region="us-east-1")

Bedrock 모델 ID 매핑:
    - gemini-flash → (Bedrock 미지원, Google API 직접 호출 필요)
    - gpt-4o-mini → (Bedrock 미지원, OpenAI API 직접 호출)
    - claude-haiku → anthropic.claude-3-haiku-20240307-v1:0
    - claude-sonnet → anthropic.claude-3-5-sonnet-20241022-v2:0
    - claude-opus → anthropic.claude-3-opus-20240229-v1:0
"""

from typing import Optional

from .base_client import BaseLLMClient, LLMResponse


# Bedrock 모델 ID 매핑
BEDROCK_MODEL_MAP = {
    "claude-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "claude-opus": "anthropic.claude-3-opus-20240229-v1:0",
    # 아래 모델들은 Bedrock에서 직접 지원하지 않으므로
    # 별도 프로바이더 클라이언트가 필요합니다.
    # "gemini-flash": "google direct",
    # "gpt-4o": "openai direct",
}


class BedrockLLMClient(BaseLLMClient):
    """
    Amazon Bedrock LLM 클라이언트.

    TODO: boto3 또는 langchain-aws ChatBedrockConverse 연동
    """

    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """
        Args:
            region: AWS 리전
            profile: AWS CLI 프로필 이름 (선택)
        """
        self.region = region
        self.profile = profile
        self._client = None  # TODO: boto3 client 초기화

        # TODO: 아래 주석 해제
        # import boto3
        # session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        # self._client = session.client(
        #     "bedrock-runtime",
        #     region_name=region,
        # )

    def generate(
        self,
        model_id: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Bedrock Converse API를 호출합니다.

        TODO: 구현 예시 (langchain-aws 사용 시)
        ```python
        from langchain_aws import ChatBedrockConverse

        bedrock_model_id = BEDROCK_MODEL_MAP.get(model_id)
        if not bedrock_model_id:
            raise ValueError(f"Bedrock에서 지원하지 않는 모델: {model_id}")

        llm = ChatBedrockConverse(
            model=bedrock_model_id,
            region_name=self.region,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = llm.invoke(messages)
        return LLMResponse(
            model_id=model_id,
            content=response.content,
            input_tokens=response.usage_metadata.get("input_tokens", 0),
            output_tokens=response.usage_metadata.get("output_tokens", 0),
            total_tokens=response.usage_metadata.get("total_tokens", 0),
            latency_ms=...,
            is_mock=False,
        )
        ```
        """
        raise NotImplementedError(
            "BedrockLLMClient는 아직 구현되지 않았습니다. "
            "AWS Bedrock 권한이 활성화되면 이 메서드를 구현하세요. "
            "현재는 MockLLMClient를 사용하세요."
        )

    def is_available(self) -> bool:
        """
        TODO: 실제 Bedrock 연결 가능 여부 확인
        """
        return False

    # TODO: 향후 추가 메서드
    # def generate_stream(self, model_id, prompt, ...): ...
    # def list_available_models(self): ...
