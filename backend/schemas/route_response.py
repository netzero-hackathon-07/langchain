"""응답 스키마 정의 - 프론트엔드로 내려줄 JSON 구조"""

from pydantic import BaseModel, Field
from typing import List


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str


# ─── Multi-Step Plan 스키마 ────────────────────────────────

class PlanRequest(BaseModel):
    """POST /plan, POST /plan/graph 요청 바디"""
    query: str = Field(..., description="복합 작업 요청 텍스트")
    policy: str = Field(default="balanced", description="운영 정책: cost_first, carbon_first, quality_first, balanced")
    baseline_model: str = Field(default="claude-sonnet", description="비교 기준 모델 (전부 이 모델로 처리했을 때 대비 절감량 계산)")


class StepDetail(BaseModel):
    """각 서브태스크 실행 결과"""
    step: int
    action: str
    task_type: str
    difficulty: str
    selected_model: str
    reason: str
    alternatives: List[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    co2_g: float
    baseline_cost_usd: float
    baseline_co2_g: float
    saved_cost_usd: float
    saved_co2_g: float
    answer: str


class PlanResponse(BaseModel):
    """POST /plan 응답 바디"""
    query: str
    policy: str
    baseline_model: str
    is_multi_step: bool
    total_steps: int
    steps: List[StepDetail]
    # 합산 지표
    total_tokens: int
    total_cost_usd: float
    total_co2_g: float
    baseline_total_cost_usd: float
    baseline_total_co2_g: float
    saved_cost_usd: float
    saved_co2_g: float
    percent_cheaper: float
    percent_less_co2: float
    # 모델 배정 요약
    model_assignment: dict
