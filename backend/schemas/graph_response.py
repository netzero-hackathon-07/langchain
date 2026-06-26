"""파이프라인 그래프 응답 스키마

노드-엣지 구조로 멀티스텝 실행 결과를 표현합니다.
프론트엔드에서 시각화(flow chart, DAG)에 바로 사용 가능한 형태.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class NodePosition(BaseModel):
    x: int
    y: int


class PipelineNode(BaseModel):
    """파이프라인의 각 스텝 (노드)"""
    id: str = Field(..., description="노드 고유 ID (node-001 형태)")
    role: str = Field(..., description="역할: searcher, coder, writer, analyst, planner, translator, reviewer")
    model: str = Field(..., description="배정된 모델 ID")
    label: str = Field(..., description="이 스텝의 행동 요약")
    task_type: str = Field(..., description="분류된 작업 유형")
    difficulty: str = Field(..., description="난이도")
    estimated_input_tokens: int
    estimated_output_tokens: int
    system_prompt_tokens: int = Field(default=150, description="시스템 프롬프트 토큰 (추정)")
    call_count: int = Field(default=1, description="이 노드의 LLM 호출 횟수")
    cost_usd: float
    co2_g: float
    baseline_cost_usd: float
    baseline_co2_g: float
    reason: str
    alternatives: List[str]
    position: NodePosition
    mock_answer: str = ""


class PipelineEdge(BaseModel):
    """노드 간 연결 (데이터 흐름)"""
    id: str = Field(..., description="엣지 고유 ID")
    source_node_id: str
    target_node_id: str
    data_transfer: str = Field(
        default="result_only",
        description="데이터 전달 방식: result_only, context_pass, full_context"
    )
    token_overhead: int = Field(
        default=100,
        description="노드 간 전달 시 추가 토큰 오버헤드"
    )


class PipelineSummary(BaseModel):
    """파이프라인 전체 요약 지표"""
    total_nodes: int
    total_tokens: int
    total_cost_usd: float
    total_co2_g: float
    baseline_total_cost_usd: float
    baseline_total_co2_g: float
    saved_cost_usd: float
    saved_co2_g: float
    percent_cheaper: float
    percent_less_co2: float
    model_assignment: Dict[str, List[str]]


class PipelineGraphResponse(BaseModel):
    """POST /plan/graph 응답 바디 — 노드-엣지 그래프 구조"""
    id: str = Field(..., description="파이프라인 고유 ID")
    name: str = Field(..., description="파이프라인 이름 (자동 생성)")
    query: str
    policy: str
    baseline_model: str
    created_at: str
    updated_at: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    summary: PipelineSummary
