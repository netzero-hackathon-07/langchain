"""탄소/비용 계산기

모델별 실측 토큰을 기반으로 비용(USD)과 CO₂(g)를 계산합니다.

CO₂ 계산 기준 (model_catalog의 co2_mg_per_token):
- Gemini 계열: 0.250 mgCO₂/token
- GPT 계열: 0.699 mgCO₂/token
- Claude Sonnet 기준: 0.872 mgCO₂/token
"""

from .model_catalog import get_model


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """모델의 비용을 계산합니다 (USD)."""
    spec = get_model(model_id)
    if not spec:
        return 0.0

    return (
        (input_tokens / 1_000_000) * spec.input_cost_per_1m
        + (output_tokens / 1_000_000) * spec.output_cost_per_1m
    )


def calculate_co2(model_id: str, total_tokens: int) -> float:
    """모델의 CO₂ 배출량을 계산합니다 (그램)."""
    spec = get_model(model_id)
    if not spec:
        return 0.0

    co2_mg = total_tokens * spec.co2_mg_per_token
    return co2_mg / 1000  # mg → g
