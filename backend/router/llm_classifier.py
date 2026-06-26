"""LLM 기반 작업 분류기 + 분해기

Claude 3.5 Haiku가 직접:
1. 복합 요청을 서브태스크로 분해
2. 각 서브태스크의 작업 유형 / 난이도 판단
3. 각 서브태스크에 최적 모델 추천

rule-based 로직 완전 대체.
"""

import json
from typing import Optional

from llm.base_client import BaseLLMClient

CLASSIFIER_SYSTEM_PROMPT = """너는 ECOCACHE의 AI 라우팅 엔진이야.
사용자의 요청을 분석해서 서브태스크로 분해하고, 각 태스크에 최적의 AI 모델을 추천해.

사용 가능한 모델 목록:
- gemini-flash: 저비용, 저탄소, 빠른 응답. 단순 질의/요약/번역/문장 수정에 적합. (CO2: 0.250mg/token, 비용: 매우 저렴)
- gpt-4o-mini: 범용 저비용 모델. 단순~중간 난이도 작업. (CO2: 0.350mg/token, 비용: 저렴)
- claude-haiku: 빠른 요약/문장 처리. 단순~중간. (CO2: 0.300mg/token, 비용: 저렴)
- gpt-4o: 균형형 고품질. 코딩/추론/기획에 적합. (CO2: 0.699mg/token, 비용: 중간)
- gemini-pro: 중상급 범용. 코딩/추론/기획. (CO2: 0.450mg/token, 비용: 중간)
- claude-sonnet: 복잡한 추론/코딩/긴 문맥. 최고 품질. (CO2: 0.872mg/token, 비용: 높음)

작업 유형 종류:
- simple_qa: 단순 질문
- summarize: 요약
- translate: 번역
- writing_edit: 문장 수정/작성
- coding: 코딩
- reasoning: 복잡한 추론/분석
- planning: 기획/창작
- sensitive: 중요/민감 답변

난이도: low, medium, high

운영 정책:
- cost_first: 비용 절감 최우선 → 가능하면 gemini-flash, gpt-4o-mini 추천
- carbon_first: 탄소 배출 최소화 → gemini-flash 우선
- quality_first: 품질 우선 → 복잡한 작업은 claude-sonnet, gpt-4o
- balanced: 균형

반드시 아래 JSON 형식으로만 응답해. 다른 텍스트 없이 JSON만:
{
  "subtasks": [
    {
      "step": 1,
      "action": "이 스텝에서 할 행동 (한국어, 짧게)",
      "task_type": "작업유형",
      "difficulty": "난이도",
      "recommended_model": "추천 모델 ID",
      "reason": "이 모델을 추천한 이유 (한국어, 1~2문장)"
    }
  ]
}

단일 작업이면 subtasks에 1개만 넣어.
복합 작업이면 논리적 순서대로 분해해서 여러 개 넣어.
각 스텝은 독립적으로 실행 가능해야 해."""


def classify_and_decompose(
    query: str,
    policy: str,
    llm_client: BaseLLMClient,
) -> dict:
    """
    LLM이 직접 요청을 분석하여 분해 + 분류 + 모델 추천을 수행합니다.

    Returns:
        {
            "subtasks": [...],
            "_classifier_input_tokens": int,   # 분류 호출에 쓴 토큰
            "_classifier_output_tokens": int,
        }
    """
    user_prompt = f"""사용자 요청: "{query}"
운영 정책: {policy}

이 요청을 분석해서 서브태스크로 분해하고, 각 태스크에 최적 모델을 추천해줘."""

    response = llm_client.generate(
        model_id="claude-haiku",  # 분류기 자체는 haiku로 호출
        prompt=user_prompt,
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
        max_tokens=1500,
        temperature=0.3,  # 분류는 일관성 있게
    )

    classifier_tokens = {
        "_classifier_input_tokens": response.input_tokens,
        "_classifier_output_tokens": response.output_tokens,
    }

    # JSON 파싱
    try:
        # 응답에서 JSON 추출
        content = response.content.strip()
        # ```json ... ``` 형태일 수 있으므로 처리
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        result.update(classifier_tokens)
        return result
    except (json.JSONDecodeError, IndexError, KeyError):
        # 파싱 실패 시 단일 태스크로 fallback
        return {
            "subtasks": [
                {
                    "step": 1,
                    "action": query[:50],
                    "task_type": "simple_qa",
                    "difficulty": "medium",
                    "recommended_model": "claude-haiku",
                    "reason": "분류 실패로 기본 모델을 배정했습니다.",
                }
            ],
            **classifier_tokens,
        }
