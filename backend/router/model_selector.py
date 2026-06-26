"""모델 선택기 - 최종 모델 선택 로직

작업 유형, 난이도, 운영 정책을 종합하여 최적 모델을 선택합니다.

점수 계산:
    final_score = quality_score * quality_weight
                + cost_score * cost_weight
                + carbon_score * carbon_weight
                + speed_score * speed_weight
                + task_fit_score

현재: rule-based score 계산
향후: LangChain Agent 기반 선택으로 교체 가능
"""

from typing import Dict, List, Tuple
from langchain_core.runnables import RunnableLambda

from .model_catalog import MODEL_CATALOG, ModelSpec
from .routing_policy import get_policy, PolicyWeights


# 난이도별 최소 품질 요구치
MIN_QUALITY_THRESHOLD = {
    "low": 0.0,
    "medium": 0.55,
    "high": 0.75,
}

# 작업 적합 보너스 점수
TASK_FIT_BONUS = 0.12


def select_model(
    task_type: str,
    difficulty: str,
    policy: str,
) -> Tuple[str, str, List[str]]:
    """
    최적 모델을 선택합니다.

    Args:
        task_type: 작업 유형
        difficulty: 난이도 (low/medium/high)
        policy: 운영 정책 이름

    Returns:
        (selected_model_id, reason, alternatives)
    """
    weights = get_policy(policy)
    min_quality = MIN_QUALITY_THRESHOLD.get(difficulty, 0.0)

    # 각 모델 점수 계산
    scores: Dict[str, float] = {}
    for model_id, spec in MODEL_CATALOG.items():
        # 최소 품질 미달 모델 필터링
        if spec.quality_score < min_quality:
            continue
        score = _compute_score(spec, task_type, difficulty, weights)
        scores[model_id] = score

    # 점수 기준 정렬
    sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if not sorted_models:
        # fallback
        return "claude-sonnet", "적합한 모델을 찾지 못해 기본 모델을 선택했습니다.", []

    selected_id = sorted_models[0][0]
    alternatives = [m[0] for m in sorted_models[1:3]]

    reason = _generate_reason(selected_id, task_type, difficulty, policy)

    return selected_id, reason, alternatives


def _compute_score(
    spec: ModelSpec,
    task_type: str,
    difficulty: str,
    weights: PolicyWeights,
) -> float:
    """모델 종합 점수 계산"""

    # 기본 가중합
    base_score = (
        spec.quality_score * weights.quality_weight
        + spec.cost_score * weights.cost_weight
        + spec.carbon_score * weights.carbon_weight
        + spec.speed_score * weights.speed_weight
    )

    # 작업 적합도 보너스
    task_fit = TASK_FIT_BONUS if task_type in spec.best_for else 0.0

    # 난이도 보정 (high 난이도에서 고품질 모델 가산)
    difficulty_bonus = 0.0
    if difficulty == "high" and spec.quality_score >= 0.80:
        difficulty_bonus = 0.08
    elif difficulty == "high" and spec.quality_score < 0.60:
        difficulty_bonus = -0.05

    return round(base_score + task_fit + difficulty_bonus, 4)


def _generate_reason(
    selected_id: str,
    task_type: str,
    difficulty: str,
    policy: str,
) -> str:
    """추천 이유를 생성합니다."""
    spec = MODEL_CATALOG[selected_id]

    policy_labels = {
        "cost_first": "비용 절감",
        "carbon_first": "탄소 배출 최소화",
        "quality_first": "응답 품질 확보",
        "balanced": "비용·탄소·품질 균형",
    }
    difficulty_labels = {"low": "낮은", "medium": "중간", "high": "높은"}
    task_labels = {
        "simple_qa": "단순 질의",
        "summarize": "요약",
        "translate": "번역",
        "writing_edit": "문장 수정",
        "coding": "코딩 보조",
        "reasoning": "복잡한 추론",
        "planning": "기획/창작",
        "sensitive": "중요/민감 답변",
    }

    task_label = task_labels.get(task_type, task_type)
    diff_label = difficulty_labels.get(difficulty, difficulty)
    policy_label = policy_labels.get(policy, "균형")

    # 비용/탄소 레벨
    cost_level = "저비용" if spec.cost_score >= 0.80 else "중비용" if spec.cost_score >= 0.40 else "고비용"
    carbon_level = "저탄소" if spec.carbon_score >= 0.80 else "중탄소" if spec.carbon_score >= 0.40 else "고탄소"

    if spec.quality_score >= 0.85:
        return (
            f"'{task_label}' 작업이며 난이도가 {diff_label} 수준입니다. "
            f"{policy_label} 정책 하에서 고성능 모델이 필요하다고 판단하여 "
            f"{spec.display_name}을 선택했습니다."
        )

    return (
        f"'{task_label}' 작업(난이도: {diff_label})에 대해 {policy_label} 정책을 적용했습니다. "
        f"{spec.display_name}은 {cost_level}·{carbon_level} 모델로, "
        f"이 작업에 충분한 성능을 제공하면서 기준 모델 대비 비용과 탄소를 절감합니다."
    )


# ─── LangChain Runnable 인터페이스 ──────────────────────────────

def _selector_runnable_fn(inputs: dict) -> dict:
    """LangChain Runnable 호환 함수"""
    selected_id, reason, alternatives = select_model(
        task_type=inputs["task_type"],
        difficulty=inputs["difficulty"],
        policy=inputs["policy"],
    )
    return {
        **inputs,
        "selected_model": selected_id,
        "reason": reason,
        "alternatives": alternatives,
    }


model_selector_runnable = RunnableLambda(_selector_runnable_fn)
