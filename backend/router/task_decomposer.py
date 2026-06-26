"""작업 분해기 (Task Decomposer)

복합 요청을 여러 서브태스크로 분해합니다.

예: "자료 찾아서 코딩해서 보고서로 만들어줘"
→ [
    { step: 1, action: "자료 검색 및 요약", task_type: "summarize" },
    { step: 2, action: "코드 작성", task_type: "coding" },
    { step: 3, action: "보고서 작성/정리", task_type: "writing_edit" },
  ]

현재: rule-based 키워드 분석으로 분해
향후: LangChain LLM 기반 분해 (경량 모델로 플래닝)
"""

from typing import List, Dict
from dataclasses import dataclass, asdict
from langchain_core.runnables import RunnableLambda


@dataclass
class SubTask:
    step: int
    action: str           # 이 스텝에서 할 행동 설명
    task_type: str        # 분류된 작업 유형
    difficulty: str       # 난이도
    description: str      # 상세 설명
    estimated_portion: float  # 전체 대비 이 스텝의 토큰 비중 (0~1)


# ─── 분해 규칙 ────────────────────────────────────────────

# 복합 행동 키워드 → 서브태스크 매핑
ACTION_PATTERNS = [
    {
        "keywords": ["찾아", "검색", "조사", "리서치", "자료", "정보", "search", "research", "find"],
        "action": "자료 검색 및 정보 수집",
        "task_type": "summarize",
        "difficulty": "low",
        "description": "관련 자료를 검색하고 핵심 정보를 추출합니다.",
        "portion": 0.20,
    },
    {
        "keywords": ["요약", "정리", "핵심", "summarize", "요점"],
        "action": "정보 요약 및 정리",
        "task_type": "summarize",
        "difficulty": "low",
        "description": "수집한 정보를 간결하게 요약합니다.",
        "portion": 0.15,
    },
    {
        "keywords": ["번역", "translate", "영어로", "한국어로"],
        "action": "번역",
        "task_type": "translate",
        "difficulty": "low",
        "description": "텍스트를 다른 언어로 번역합니다.",
        "portion": 0.15,
    },
    {
        "keywords": ["코딩", "코드", "구현", "개발", "프로그래밍", "code", "implement", "develop", "함수", "클래스"],
        "action": "코드 작성",
        "task_type": "coding",
        "difficulty": "medium",
        "description": "요구사항에 맞는 코드를 작성합니다.",
        "portion": 0.35,
    },
    {
        "keywords": ["리팩토링", "refactor", "최적화", "개선"],
        "action": "코드 리팩토링/최적화",
        "task_type": "coding",
        "difficulty": "medium",
        "description": "기존 코드를 개선하고 최적화합니다.",
        "portion": 0.25,
    },
    {
        "keywords": ["테스트", "test", "검증", "확인"],
        "action": "테스트 및 검증",
        "task_type": "coding",
        "difficulty": "low",
        "description": "작성된 코드의 정확성을 검증합니다.",
        "portion": 0.15,
    },
    {
        "keywords": ["설계", "아키텍처", "architecture", "구조", "design", "시스템"],
        "action": "시스템 설계",
        "task_type": "reasoning",
        "difficulty": "high",
        "description": "시스템 아키텍처를 설계하고 구조를 결정합니다.",
        "portion": 0.30,
    },
    {
        "keywords": ["분석", "비교", "평가", "analyze", "compare"],
        "action": "분석 및 비교",
        "task_type": "reasoning",
        "difficulty": "medium",
        "description": "여러 옵션을 분석하고 비교 평가합니다.",
        "portion": 0.25,
    },
    {
        "keywords": ["보고서", "문서", "레포트", "report", "document", "작성"],
        "action": "보고서/문서 작성",
        "task_type": "writing_edit",
        "difficulty": "medium",
        "description": "결과를 정리하여 보고서 또는 문서로 작성합니다.",
        "portion": 0.25,
    },
    {
        "keywords": ["다듬", "교정", "수정", "polish", "edit", "고쳐"],
        "action": "문서 교정 및 다듬기",
        "task_type": "writing_edit",
        "difficulty": "low",
        "description": "작성된 문서의 문체와 맞춤법을 교정합니다.",
        "portion": 0.10,
    },
    {
        "keywords": ["기획", "전략", "플랜", "plan", "브레인스토밍", "아이디어"],
        "action": "기획 및 전략 수립",
        "task_type": "planning",
        "difficulty": "medium",
        "description": "전략을 수립하고 실행 계획을 만듭니다.",
        "portion": 0.25,
    },
    {
        "keywords": ["발표", "프레젠테이션", "presentation", "슬라이드"],
        "action": "발표 자료 구성",
        "task_type": "planning",
        "difficulty": "medium",
        "description": "프레젠테이션 구조와 내용을 구성합니다.",
        "portion": 0.20,
    },
]


def decompose_task(query: str) -> List[SubTask]:
    """
    복합 요청을 서브태스크 리스트로 분해합니다.

    단일 작업이면 서브태스크 1개만 반환합니다.
    복합 작업이면 감지된 행동만큼 분해합니다.
    """
    query_lower = query.lower()
    matched_actions = []

    for pattern in ACTION_PATTERNS:
        hits = sum(1 for kw in pattern["keywords"] if kw in query_lower)
        if hits > 0:
            matched_actions.append((hits, pattern))

    # 매칭된 것이 없거나 1개뿐이면 단일 작업
    if len(matched_actions) <= 1:
        # 단일 태스크 — 기존 분류기에 위임
        from .task_classifier import classify_task
        task_type, difficulty = classify_task(query)
        return [
            SubTask(
                step=1,
                action=query[:50],
                task_type=task_type,
                difficulty=difficulty,
                description=query,
                estimated_portion=1.0,
            )
        ]

    # 중복 task_type 제거하면서 순서 유지 (같은 유형이 여러 번 잡히면 점수 높은 것만)
    seen_types = {}
    for score, pattern in sorted(matched_actions, key=lambda x: -x[0]):
        key = pattern["action"]
        if key not in seen_types:
            seen_types[key] = pattern

    # 서브태스크 리스트 생성
    subtasks = []
    portions = []
    for i, (action_name, pattern) in enumerate(seen_types.items(), 1):
        portions.append(pattern["portion"])
        subtasks.append(SubTask(
            step=i,
            action=pattern["action"],
            task_type=pattern["task_type"],
            difficulty=pattern["difficulty"],
            description=pattern["description"],
            estimated_portion=pattern["portion"],
        ))

    # 비중 정규화 (합이 1이 되도록)
    total_portion = sum(s.estimated_portion for s in subtasks)
    if total_portion > 0:
        for s in subtasks:
            s.estimated_portion = round(s.estimated_portion / total_portion, 3)

    return subtasks


# ─── LangChain Runnable ──────────────────────────────────

def _decompose_runnable_fn(inputs: dict) -> dict:
    """LangChain Runnable 호환"""
    subtasks = decompose_task(inputs["query"])
    return {
        **inputs,
        "subtasks": [asdict(s) for s in subtasks],
        "is_multi_step": len(subtasks) > 1,
    }


task_decomposer_runnable = RunnableLambda(_decompose_runnable_fn)
