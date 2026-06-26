"""모델 카탈로그 - 모델별 메타데이터 관리

각 모델의 비용, 탄소 배출, 품질 점수, 속성을 정의합니다.
향후 DB나 외부 설정 파일로 분리 가능합니다.

CO₂ 계산 기준:
- Gemini 계열: 0.250 mgCO₂/token
- GPT 계열: 0.699 mgCO₂/token
- Claude 계열: 0.872 mgCO₂/token
- Gemma 계열 (로컬/경량): 0.120 mgCO₂/token
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ModelSpec:
    model_id: str
    display_name: str
    provider: str
    input_cost_per_1m: float      # USD per 1M input tokens
    output_cost_per_1m: float     # USD per 1M output tokens
    co2_mg_per_token: float       # mgCO₂ per token
    quality_score: float          # 0~1
    speed_score: float            # 0~1
    carbon_score: float           # 0~1 (높을수록 친환경)
    cost_score: float             # 0~1 (높을수록 저렴)
    best_for: List[str]           # 적합 작업 유형


MODEL_CATALOG: Dict[str, ModelSpec] = {
    "gemini-flash": ModelSpec(
        model_id="gemini-flash",
        display_name="Gemini Flash",
        provider="google",
        input_cost_per_1m=0.075,
        output_cost_per_1m=0.30,
        co2_mg_per_token=0.250,
        quality_score=0.55,
        speed_score=0.95,
        carbon_score=0.95,
        cost_score=0.95,
        best_for=["simple_qa", "summarize", "translate", "writing_edit"],
    ),
    "gpt-4o-mini": ModelSpec(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider="openai",
        input_cost_per_1m=0.15,
        output_cost_per_1m=0.60,
        co2_mg_per_token=0.350,
        quality_score=0.65,
        speed_score=0.85,
        carbon_score=0.82,
        cost_score=0.90,
        best_for=["simple_qa", "summarize", "translate", "writing_edit", "coding"],
    ),
    "claude-haiku": ModelSpec(
        model_id="claude-haiku",
        display_name="Claude Haiku",
        provider="anthropic",
        input_cost_per_1m=0.25,
        output_cost_per_1m=1.25,
        co2_mg_per_token=0.300,
        quality_score=0.60,
        speed_score=0.90,
        carbon_score=0.88,
        cost_score=0.85,
        best_for=["summarize", "writing_edit", "simple_qa", "translate"],
    ),
    "gpt-4o": ModelSpec(
        model_id="gpt-4o",
        display_name="GPT-4o",
        provider="openai",
        input_cost_per_1m=2.50,
        output_cost_per_1m=10.00,
        co2_mg_per_token=0.699,
        quality_score=0.85,
        speed_score=0.70,
        carbon_score=0.45,
        cost_score=0.35,
        best_for=["coding", "reasoning", "planning", "sensitive"],
    ),
    "gemini-pro": ModelSpec(
        model_id="gemini-pro",
        display_name="Gemini Pro",
        provider="google",
        input_cost_per_1m=1.25,
        output_cost_per_1m=5.00,
        co2_mg_per_token=0.450,
        quality_score=0.78,
        speed_score=0.75,
        carbon_score=0.70,
        cost_score=0.55,
        best_for=["coding", "reasoning", "planning", "summarize"],
    ),
    "claude-sonnet": ModelSpec(
        model_id="claude-sonnet",
        display_name="Claude Sonnet",
        provider="anthropic",
        input_cost_per_1m=3.00,
        output_cost_per_1m=15.00,
        co2_mg_per_token=0.872,
        quality_score=0.92,
        speed_score=0.60,
        carbon_score=0.30,
        cost_score=0.20,
        best_for=["reasoning", "coding", "planning", "sensitive"],
    ),
    "claude-opus": ModelSpec(
        model_id="claude-opus",
        display_name="Claude Opus",
        provider="anthropic",
        input_cost_per_1m=15.00,
        output_cost_per_1m=75.00,
        co2_mg_per_token=0.950,
        quality_score=0.97,
        speed_score=0.40,
        carbon_score=0.15,
        cost_score=0.05,
        best_for=["reasoning", "sensitive", "planning"],
    ),
    "gemma-4-e2b": ModelSpec(
        model_id="gemma-4-e2b",
        display_name="Gemma 4 E2B",
        provider="google-open",
        input_cost_per_1m=0.00,
        output_cost_per_1m=0.00,
        co2_mg_per_token=0.120,
        quality_score=0.40,
        speed_score=0.92,
        carbon_score=0.98,
        cost_score=1.00,
        best_for=["simple_qa", "translate", "summarize"],
    ),
    "gemma-4-27b-a4b": ModelSpec(
        model_id="gemma-4-27b-a4b",
        display_name="Gemma 4 27B",
        provider="google-open",
        input_cost_per_1m=0.00,
        output_cost_per_1m=0.00,
        co2_mg_per_token=0.180,
        quality_score=0.58,
        speed_score=0.80,
        carbon_score=0.96,
        cost_score=1.00,
        best_for=["simple_qa", "summarize", "translate", "writing_edit", "coding"],
    ),
}

# Baseline 모델
BASELINE_MODEL_ID = "claude-sonnet"


def get_model(model_id: str) -> Optional[ModelSpec]:
    return MODEL_CATALOG.get(model_id)


def get_all_models() -> Dict[str, ModelSpec]:
    return MODEL_CATALOG


def get_baseline() -> ModelSpec:
    return MODEL_CATALOG[BASELINE_MODEL_ID]


def get_model_ids() -> List[str]:
    return list(MODEL_CATALOG.keys())
