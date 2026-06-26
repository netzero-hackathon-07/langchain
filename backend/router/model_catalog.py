"""모델 카탈로그 - data/models.json 로드 + CO₂ 추정치 결합

가격/메타데이터는 팀 공통 데이터(data/models.json)를 단일 출처로 사용한다.
data/models.json에는 CO₂ 정보가 없으므로, provider·tier·category 기준으로
탄소 배출 추정치(co2_mg_per_token)를 별도로 입힌다.

CO₂ 추정 근거 (mgCO₂/token):
- 모델 규모(category/tier)가 클수록, 추론(reasoning) 계열일수록 연산량↑ → CO₂↑
- provider별 데이터센터 효율 차이를 베이스로 반영
- 참고 기준: Gemini 0.250 / GPT 0.699 / Claude Sonnet 0.872
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# data/models.json 경로
_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "models.json",
)


# ─── CO₂ 추정치 (mgCO₂ / token) ────────────────────────────────
# data/models.json에 탄소 정보가 없어 별도 추정. provider·규모 기준.
CO2_MG_PER_TOKEN: Dict[str, float] = {
    # OpenAI
    "gpt-4o": 0.699,
    "gpt-4o-mini": 0.300,
    "gpt-4.1": 0.720,
    "gpt-4.1-mini": 0.330,
    "gpt-4.1-nano": 0.150,
    "gpt-5": 0.820,
    "gpt-5-mini": 0.280,
    "o3": 1.100,          # reasoning 계열 — 연산량 많음
    "o4-mini": 0.520,     # reasoning 경량
    # Anthropic
    "claude-opus-4": 0.950,
    "claude-sonnet-4": 0.872,
    "claude-3-5-haiku": 0.300,
    # Google
    "gemini-2.0-flash": 0.250,
    # AWS Bedrock
    "writer-palmyra-x4": 0.700,
    "writer-palmyra-x5": 0.450,
    "amazon-nova-2-omni-preview": 0.400,
    "amazon-nova-2-pro-trial": 0.800,
}

# CO₂ 미정의 모델용 fallback (tier 기준)
_CO2_BY_TIER = {"economy": 0.300, "balanced": 0.500, "advanced": 0.850}


@dataclass
class ModelSpec:
    model_id: str
    display_name: str
    provider: str
    input_cost_per_1m: float       # USD per 1M input tokens
    output_cost_per_1m: float      # USD per 1M output tokens
    co2_mg_per_token: float        # mgCO₂ per token (추정치)
    category: str                  # flagship / small / nano / reasoning / multimodal
    tier: str                      # economy / balanced / advanced
    strengths: List[str] = field(default_factory=list)
    recommended_for: List[str] = field(default_factory=list)
    provider_route: str = "direct_api"


def _load_catalog() -> Dict[str, ModelSpec]:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    catalog: Dict[str, ModelSpec] = {}
    for model_id, m in raw.items():
        if not m.get("enabled", True):
            continue
        tier = m.get("tier", "balanced")
        co2 = CO2_MG_PER_TOKEN.get(model_id, _CO2_BY_TIER.get(tier, 0.500))
        catalog[model_id] = ModelSpec(
            model_id=m["model_id"],
            display_name=m["display_name"],
            provider=m["provider"],
            input_cost_per_1m=m["input_usd_per_1m_tokens"],
            output_cost_per_1m=m["output_usd_per_1m_tokens"],
            co2_mg_per_token=co2,
            category=m.get("category", ""),
            tier=tier,
            strengths=m.get("strengths", []),
            recommended_for=m.get("recommended_for", []),
            provider_route=m.get("provider_route", "direct_api"),
        )
    return catalog


MODEL_CATALOG: Dict[str, ModelSpec] = _load_catalog()

# Baseline 모델 (비교 기준) - "전부 이 고성능 모델로 처리했다면" 가정
BASELINE_MODEL_ID = "claude-opus-4"


def get_model(model_id: str) -> Optional[ModelSpec]:
    return MODEL_CATALOG.get(model_id)


def get_all_models() -> Dict[str, ModelSpec]:
    return MODEL_CATALOG


def get_baseline() -> ModelSpec:
    return MODEL_CATALOG[BASELINE_MODEL_ID]


def get_model_ids() -> List[str]:
    return list(MODEL_CATALOG.keys())
