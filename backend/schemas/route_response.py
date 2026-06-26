"""응답 스키마 정의 - 프론트엔드로 내려줄 JSON 구조"""

from pydantic import BaseModel, Field
from typing import List, Optional


class RouteRequest(BaseModel):
    """POST /route 요청 바디"""
    query: str = Field(..., description="사용자의 요청 텍스트")
    policy: str = Field(default="balanced", description="운영 정책: cost_first, carbon_first, quality_first, balanced")
    baseline_model: str = Field(default="claude-sonnet", description="비교 기준 모델")


class TokenEstimate(BaseModel):
    input: int
    output: int
    total: int


class CostEstimate(BaseModel):
    selected_usd: float
    baseline_usd: float
    saved_usd: float
    percent_cheaper: float


class CarbonEstimate(BaseModel):
    selected_g: float
    baseline_g: float
    saved_g: float
    percent_less_co2: float


class RouteResponse(BaseModel):
    """POST /route 응답 바디"""
    query: str
    task_type: str
    difficulty: str
    policy: str
    baseline_model: str
    selected_model: str
    reason: str
    estimated_tokens: TokenEstimate
    cost: CostEstimate
    carbon: CarbonEstimate
    alternatives: List[str]
    mock_answer: str


class HealthResponse(BaseModel):
    service: str
    status: str
    version: str


# ─── Multi-Step Plan 스키마 ────────────────────────────────

class PlanRequest(BaseModel):
    """POST /plan 요청 바디"""
    query: str = Field(..., description="복합 작업 요청 텍스트")
    policy: str = Field(default="balanced", description="운영 정책")
    baseline_model: str = Field(default="claude-sonnet", description="비교 기준 모델")


class StepDetail(BaseModel):
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
    mock_answer: str


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
