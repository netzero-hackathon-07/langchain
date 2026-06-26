"""라우팅 정책 관리

정책별 가중치를 정의합니다.
운영 정책 메타데이터(라벨/설명)를 /policies 엔드포인트에서 제공합니다.
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class PolicyWeights:
    quality_weight: float
    cost_weight: float
    carbon_weight: float
    speed_weight: float
    label: str
    description: str


POLICIES: Dict[str, PolicyWeights] = {
    "cost_first": PolicyWeights(
        quality_weight=0.15,
        cost_weight=0.50,
        carbon_weight=0.20,
        speed_weight=0.15,
        label="비용 우선",
        description="비용 절감을 최우선으로 합니다.",
    ),
    "carbon_first": PolicyWeights(
        quality_weight=0.20,
        cost_weight=0.15,
        carbon_weight=0.50,
        speed_weight=0.15,
        label="탄소 우선",
        description="CO₂ 배출 최소화를 최우선으로 합니다.",
    ),
    "quality_first": PolicyWeights(
        quality_weight=0.55,
        cost_weight=0.10,
        carbon_weight=0.10,
        speed_weight=0.25,
        label="품질 우선",
        description="응답 품질을 최우선으로 합니다.",
    ),
    "balanced": PolicyWeights(
        quality_weight=0.30,
        cost_weight=0.25,
        carbon_weight=0.25,
        speed_weight=0.20,
        label="균형",
        description="비용, 탄소, 품질, 속도를 균형 있게 고려합니다.",
    ),
}


def get_policy(policy_name: str) -> PolicyWeights:
    """정책 이름으로 가중치를 반환합니다. 없으면 balanced 반환."""
    return POLICIES.get(policy_name, POLICIES["balanced"])


def get_all_policies() -> Dict[str, PolicyWeights]:
    return POLICIES
