"""플랜 실행기 (Plan Executor)

분해된 서브태스크를 순차적으로 실행합니다.
각 스텝마다 최적 모델을 배정하고, mock LLM을 호출하여 시뮬레이션합니다.
최종적으로 전체 스텝의 절감량을 합산합니다.

흐름:
  query → decompose → [classify + select + execute] × N → aggregate

이것이 ECOCACHE의 핵심 가치:
  "복합 작업을 쪼개서 각 스텝마다 최적 모델을 배정하면,
   전부 고성능 모델 하나로 처리하는 것보다 얼마나 절감되는가?"
"""

from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from .task_decomposer import SubTask, decompose_task
from .model_selector import select_model
from .carbon_estimator import (
    estimate_tokens,
    calculate_cost,
    calculate_co2,
    calculate_savings,
)
from .model_catalog import BASELINE_MODEL_ID, get_model


@dataclass
class StepResult:
    """각 스텝의 실행 결과"""
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


@dataclass
class PlanResult:
    """전체 플랜 실행 결과"""
    query: str
    policy: str
    baseline_model: str
    is_multi_step: bool
    total_steps: int
    steps: List[StepResult]
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
    model_assignment: Dict[str, List[str]]  # model -> [step actions]


def execute_plan(
    query: str,
    policy: str,
    baseline_model: str = BASELINE_MODEL_ID,
    llm_client=None,
) -> PlanResult:
    """
    복합 요청을 분해하고, 각 스텝마다 최적 모델을 배정하여 시뮬레이션합니다.

    Args:
        query: 사용자 복합 요청
        policy: 운영 정책
        baseline_model: 비교 기준 모델
        llm_client: LLM 클라이언트 (mock 또는 실제)

    Returns:
        PlanResult: 전체 실행 결과 및 절감량
    """
    # 1. 작업 분해
    subtasks = decompose_task(query)

    # 2. 전체 토큰 예산 추정 (쿼리 길이 + 복잡도 기반)
    total_budget_input, total_budget_output = estimate_tokens(
        query,
        "reasoning" if len(subtasks) > 1 else subtasks[0].task_type,
        "high" if len(subtasks) > 2 else "medium",
    )
    total_budget = total_budget_input + total_budget_output

    # 3. 각 스텝 실행
    steps: List[StepResult] = []
    model_assignment: Dict[str, List[str]] = {}

    for subtask in subtasks:
        step_result = _execute_step(
            subtask=subtask,
            total_budget=total_budget,
            policy=policy,
            baseline_model=baseline_model,
            llm_client=llm_client,
        )
        steps.append(step_result)

        # 모델 배정 추적
        if step_result.selected_model not in model_assignment:
            model_assignment[step_result.selected_model] = []
        model_assignment[step_result.selected_model].append(step_result.action)

    # 4. 합산
    total_tokens = sum(s.total_tokens for s in steps)
    total_cost = sum(s.cost_usd for s in steps)
    total_co2 = sum(s.co2_g for s in steps)
    baseline_total_cost = sum(s.baseline_cost_usd for s in steps)
    baseline_total_co2 = sum(s.baseline_co2_g for s in steps)
    saved_cost = baseline_total_cost - total_cost
    saved_co2 = baseline_total_co2 - total_co2
    pct_cheaper = round((saved_cost / baseline_total_cost) * 100, 1) if baseline_total_cost > 0 else 0.0
    pct_less_co2 = round((saved_co2 / baseline_total_co2) * 100, 1) if baseline_total_co2 > 0 else 0.0

    return PlanResult(
        query=query,
        policy=policy,
        baseline_model=baseline_model,
        is_multi_step=len(subtasks) > 1,
        total_steps=len(subtasks),
        steps=steps,
        total_tokens=total_tokens,
        total_cost_usd=round(total_cost, 6),
        total_co2_g=round(total_co2, 6),
        baseline_total_cost_usd=round(baseline_total_cost, 6),
        baseline_total_co2_g=round(baseline_total_co2, 6),
        saved_cost_usd=round(saved_cost, 6),
        saved_co2_g=round(saved_co2, 6),
        percent_cheaper=pct_cheaper,
        percent_less_co2=pct_less_co2,
        model_assignment=model_assignment,
    )


def _execute_step(
    subtask: SubTask,
    total_budget: int,
    policy: str,
    baseline_model: str,
    llm_client=None,
) -> StepResult:
    """서브태스크 하나를 실행합니다."""

    # 이 스텝에 할당된 토큰 예산
    step_input = max(int(total_budget * subtask.estimated_portion * 0.3), 20)
    step_output = max(int(total_budget * subtask.estimated_portion * 0.7), 50)

    # 난이도 기반 보정 (작업별 최소 출력)
    min_outputs = {"coding": 200, "reasoning": 300, "planning": 200}
    min_out = min_outputs.get(subtask.task_type, 80)
    step_output = max(step_output, min_out)

    step_total = step_input + step_output

    # 모델 선택
    selected_model, reason, alternatives = select_model(
        subtask.task_type, subtask.difficulty, policy
    )

    # 비용/CO₂ 계산
    cost = calculate_cost(selected_model, step_input, step_output)
    co2 = calculate_co2(selected_model, step_total)
    baseline_cost = calculate_cost(baseline_model, step_input, step_output)
    baseline_co2 = calculate_co2(baseline_model, step_total)

    # Mock LLM 호출
    mock_answer = ""
    if llm_client:
        response = llm_client.generate(
            model_id=selected_model,
            prompt=f"[Step {subtask.step}] {subtask.action}: {subtask.description}",
            max_tokens=step_output,
        )
        mock_answer = response.content

    return StepResult(
        step=subtask.step,
        action=subtask.action,
        task_type=subtask.task_type,
        difficulty=subtask.difficulty,
        selected_model=selected_model,
        reason=reason,
        alternatives=alternatives,
        input_tokens=step_input,
        output_tokens=step_output,
        total_tokens=step_total,
        cost_usd=round(cost, 6),
        co2_g=round(co2, 6),
        baseline_cost_usd=round(baseline_cost, 6),
        baseline_co2_g=round(baseline_co2, 6),
        saved_cost_usd=round(max(baseline_cost - cost, 0), 6),
        saved_co2_g=round(max(baseline_co2 - co2, 0), 6),
        mock_answer=mock_answer,
    )
