"""탄소/비용 절감량 계산기

선택된 모델과 baseline 모델을 비교하여 절감량을 계산합니다.

CO₂ 계산 기준:
- Gemini 계열: 0.250 mgCO₂/token
- GPT 계열: 0.699 mgCO₂/token
- Claude-3.7 Sonnet 기준: 0.872 mgCO₂/token
"""

from typing import Dict, Tuple
from .model_catalog import get_model, ModelSpec


def estimate_tokens(query: str, task_type: str, difficulty: str) -> Tuple[int, int]:
    """
    예상 토큰 수를 추정합니다.

    Returns:
        (input_tokens, output_tokens)
    """
    # 입력 토큰: 한국어 약 1글자 = 2~3 토큰 기준
    input_tokens = max(len(query) * 2, 20)

    # 출력 토큰: 작업 유형과 난이도에 따라 차등
    output_map = {
        "simple_qa":     {"low": 100, "medium": 250, "high": 500},
        "summarize":     {"low": 150, "medium": 300, "high": 600},
        "translate":     {"low": 120, "medium": 250, "high": 500},
        "writing_edit":  {"low": 100, "medium": 200, "high": 400},
        "coding":        {"low": 200, "medium": 500, "high": 1200},
        "reasoning":     {"low": 300, "medium": 700, "high": 1500},
        "planning":      {"low": 250, "medium": 500, "high": 1000},
        "sensitive":     {"low": 200, "medium": 400, "high": 900},
    }

    output_tokens = output_map.get(task_type, {}).get(difficulty, 250)
    return input_tokens, output_tokens


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """모델의 예상 비용을 계산합니다 (USD)."""
    spec = get_model(model_id)
    if not spec:
        return 0.0

    cost = (
        (input_tokens / 1_000_000) * spec.input_cost_per_1m
        + (output_tokens / 1_000_000) * spec.output_cost_per_1m
    )
    return cost


def calculate_co2(model_id: str, total_tokens: int) -> float:
    """모델의 예상 CO₂ 배출량을 계산합니다 (그램)."""
    spec = get_model(model_id)
    if not spec:
        return 0.0

    co2_mg = total_tokens * spec.co2_mg_per_token
    return co2_mg / 1000  # mg → g


def calculate_savings(
    selected_model_id: str,
    baseline_model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> Dict:
    """
    선택 모델과 기준 모델을 비교하여 절감량을 계산합니다.

    Returns:
        {
            "estimated_tokens": {"input", "output", "total"},
            "cost": {"selected_usd", "baseline_usd", "saved_usd", "percent_cheaper"},
            "carbon": {"selected_g", "baseline_g", "saved_g", "percent_less_co2"},
        }
    """
    total_tokens = input_tokens + output_tokens

    # 비용 계산
    selected_cost = calculate_cost(selected_model_id, input_tokens, output_tokens)
    baseline_cost = calculate_cost(baseline_model_id, input_tokens, output_tokens)
    cost_saved = max(baseline_cost - selected_cost, 0)
    percent_cheaper = (
        round((cost_saved / baseline_cost) * 100, 1) if baseline_cost > 0 else 0.0
    )

    # CO₂ 계산
    selected_co2 = calculate_co2(selected_model_id, total_tokens)
    baseline_co2 = calculate_co2(baseline_model_id, total_tokens)
    co2_saved = max(baseline_co2 - selected_co2, 0)
    percent_less_co2 = (
        round((co2_saved / baseline_co2) * 100, 1) if baseline_co2 > 0 else 0.0
    )

    return {
        "estimated_tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens,
        },
        "cost": {
            "selected_usd": round(selected_cost, 6),
            "baseline_usd": round(baseline_cost, 6),
            "saved_usd": round(cost_saved, 6),
            "percent_cheaper": percent_cheaper,
        },
        "carbon": {
            "selected_g": round(selected_co2, 6),
            "baseline_g": round(baseline_co2, 6),
            "saved_g": round(co2_saved, 6),
            "percent_less_co2": percent_less_co2,
        },
    }
