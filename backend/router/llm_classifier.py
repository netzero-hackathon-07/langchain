"""LLM 기반 작업 분류기 + 분해기

Claude Haiku 4.5가 직접:
1. 복합 요청을 서브태스크로 분해
2. 각 서브태스크의 작업 유형 / 난이도 판단
3. data/models.json 전체 카탈로그(18종) 중에서 최적 모델 추천 + 상세 근거

모델 목록은 model_catalog에서 동적으로 생성하므로,
data/models.json만 갱신하면 프롬프트에도 자동 반영된다.
"""

import json
from typing import Optional

from llm.base_client import BaseLLMClient
from .model_catalog import get_all_models, BASELINE_MODEL_ID


def _build_model_catalog_text() -> str:
    """카탈로그를 프롬프트용 텍스트로 변환 (가격·탄소·강점 포함)."""
    lines = []
    for mid, spec in get_all_models().items():
        strengths = ", ".join(spec.strengths) if spec.strengths else "-"
        rec = ", ".join(spec.recommended_for) if spec.recommended_for else "-"
        lines.append(
            f"- {mid} ({spec.display_name}, {spec.provider}) | "
            f"tier: {spec.tier} / category: {spec.category} | "
            f"입력 ${spec.input_cost_per_1m}/1M · 출력 ${spec.output_cost_per_1m}/1M · "
            f"CO2 {spec.co2_mg_per_token}mg/token | "
            f"강점: {strengths} | 적합: {rec}"
        )
    return "\n".join(lines)


def _build_system_prompt() -> str:
    catalog_text = _build_model_catalog_text()
    return f"""너는 ECOCACHE의 AI 라우팅 엔진이다.
사용자의 요청을 분석해 실행 가능한 서브태스크로 분해하고,
각 태스크마다 아래 모델 카탈로그에서 가장 적합한 모델 하나를 선택한다.

[모델 카탈로그] (이 목록 안의 model_id만 사용할 것)
{catalog_text}

[작업 유형] simple_qa, summarize, translate, writing_edit, coding, reasoning, planning, sensitive
[난이도] low, medium, high

[운영 정책별 선택 가이드]
- cost_first: 비용을 최우선. 같은 품질이면 입력/출력 단가가 낮은 모델을 적극 선택 (nano/economy tier 우대)
- carbon_first: CO2 배출 최소화 우선. co2_mg/token이 낮은 모델을 우대 (Gemini Flash, nano 계열 등)
- quality_first: 품질 최우선. 복잡한 작업은 advanced tier(GPT-5, o3, Claude Opus 4 등)를 선택
- balanced: 작업 난이도에 비례해 합리적으로 선택. 단순 작업엔 저비용, 복잡한 작업에만 고성능

[모델 선택 원칙]
1. 작업 난이도와 모델 tier를 매칭한다. low→economy/nano, medium→balanced, high→advanced
2. 단순 작업(요약/번역/추출/분류)에 flagship/advanced 모델을 쓰지 마라. 명백한 낭비다.
3. 코딩·추론·분석엔 해당 강점(strengths)을 가진 모델을 우선한다.
4. 가능한 한 서브태스크마다 다른 모델을 배정해 다양성을 확보한다 (단, 정책과 작업 성격에 맞을 때만).
5. reason에는 반드시 다음을 포함한다:
   - 왜 이 작업에 이 tier가 적절한지
   - 다른 후보 대비 비용 또는 탄소 측면의 이점
   - 이 모델의 어떤 강점이 작업과 맞는지

[출력 형식] 반드시 아래 JSON만 출력. 다른 텍스트 금지.
{{
  "subtasks": [
    {{
      "step": 1,
      "action": "이 스텝에서 수행할 구체적 행동 (한국어, 명확하게)",
      "task_type": "작업유형",
      "difficulty": "난이도",
      "recommended_model": "카탈로그의 model_id",
      "reason": "이 모델을 선택한 상세한 근거 (한국어, 2~3문장, 비용·탄소·강점 언급)"
    }}
  ]
}}

단일 작업이면 subtasks에 1개, 복합 작업이면 논리적 순서로 여러 개로 분해한다.
각 스텝은 독립적으로 실행 가능해야 한다."""


def classify_and_decompose(
    query: str,
    policy: str,
    llm_client: BaseLLMClient,
) -> dict:
    """
    LLM이 직접 요청을 분석하여 분해 + 분류 + 모델 추천을 수행한다.

    Returns:
        {
            "subtasks": [
                {"step", "action", "task_type", "difficulty",
                 "recommended_model", "reason"}, ...
            ],
            "_classifier_input_tokens": int,
            "_classifier_output_tokens": int,
        }
    """
    system_prompt = _build_system_prompt()
    user_prompt = f"""사용자 요청: "{query}"
운영 정책: {policy}

이 요청을 서브태스크로 분해하고, 각 태스크에 카탈로그의 최적 모델을 배정해줘.
각 선택의 근거를 비용·탄소·강점 관점에서 구체적으로 설명해줘."""

    response = llm_client.generate(
        model_id="claude-haiku",
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=2000,
        temperature=0.4,
    )

    classifier_tokens = {
        "_classifier_input_tokens": response.input_tokens,
        "_classifier_output_tokens": response.output_tokens,
    }

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        result.update(classifier_tokens)
        return result
    except (json.JSONDecodeError, IndexError, KeyError):
        return {
            "subtasks": [
                {
                    "step": 1,
                    "action": query[:50],
                    "task_type": "simple_qa",
                    "difficulty": "medium",
                    "recommended_model": "claude-3-5-haiku",
                    "reason": "분류에 실패하여 기본 경량 모델을 배정했습니다.",
                }
            ],
            **classifier_tokens,
        }
