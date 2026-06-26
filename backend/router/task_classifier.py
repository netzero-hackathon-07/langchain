"""작업 유형 분류기

사용자 입력을 분석하여 task_type과 difficulty를 판단합니다.

현재: rule-based keyword matching
향후: LangChain Runnable (경량 LLM 기반 분류)로 교체 가능

LangChain 교체 시:
    from langchain_core.runnables import RunnableSequence
    classifier_chain = prompt | llm | output_parser
    result = classifier_chain.invoke({"query": query})
"""

from typing import Tuple
from langchain_core.runnables import RunnableLambda


# ─── 키워드 매핑 ────────────────────────────────────────────

TASK_KEYWORDS = {
    "simple_qa": [
        "뭐야", "알려줘", "무엇", "언제", "어디", "누구", "왜", "어떻게",
        "what", "when", "where", "who", "why", "how", "tell me", "explain",
        "정의", "의미", "차이", "뜻", "개념"
    ],
    "summarize": [
        "요약", "줄여", "정리", "핵심", "summary", "summarize", "간단히",
        "짧게", "브리핑", "요점", "tl;dr"
    ],
    "translate": [
        "번역", "translate", "영어로", "한국어로", "일본어로", "중국어로",
        "영문", "국문", "통역", "in english", "in korean"
    ],
    "writing_edit": [
        "고쳐", "수정", "다듬", "교정", "맞춤법", "자연스럽게", "rewrite",
        "polish", "edit", "proofread", "톤", "문법", "이메일", "문장"
    ],
    "coding": [
        "코드", "코딩", "함수", "구현", "리팩토링", "버그", "디버그",
        "code", "function", "implement", "refactor", "debug", "api",
        "프로그래밍", "개발", "스크립트", "알고리즘", "클래스", "class",
        "python", "java", "typescript", "react"
    ],
    "reasoning": [
        "분석", "비교", "평가", "설계", "아키텍처", "architecture",
        "최적화", "전략", "추론", "reason", "analyze", "compare",
        "시스템", "구조", "패턴", "트레이드오프", "장단점"
    ],
    "planning": [
        "기획", "작성", "창작", "아이디어", "브레인스토밍", "스토리",
        "시나리오", "기획서", "제안서", "creative", "brainstorm",
        "콘텐츠", "마케팅", "카피", "전략", "플랜", "로드맵"
    ],
    "sensitive": [
        "법률", "의료", "금융", "계약", "규정", "보안", "개인정보",
        "legal", "medical", "financial", "compliance", "security",
        "민감", "정확히", "법적", "세금", "진단", "처방"
    ],
}

DIFFICULTY_KEYWORDS = {
    "high": [
        "설계", "아키텍처", "architecture", "시스템", "전체", "복잡",
        "대규모", "최적화", "멀티", "분산", "마이크로서비스", "심층",
        "상세하게", "완전한", "포괄적", "enterprise", "production"
    ],
    "medium": [
        "리팩토링", "비교", "분석", "구현", "개선", "통합",
        "연동", "테스트", "배포", "설정", "migration", "integration"
    ],
    "low": [
        "간단", "짧게", "빠르게", "하나만", "단순", "기본",
        "simple", "quick", "brief", "basic", "한 줄"
    ],
}


def classify_task(query: str) -> Tuple[str, str]:
    """
    사용자 입력을 분석하여 (task_type, difficulty)를 반환합니다.

    Returns:
        tuple: (task_type, difficulty)
    """
    query_lower = query.lower()

    # 1. 작업 유형 분류
    scores = {}
    for task_type, keywords in TASK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[task_type] = score

    task_type = max(scores, key=scores.get) if scores else "simple_qa"

    # 2. 난이도 판단
    difficulty = _estimate_difficulty(query_lower, task_type)

    return task_type, difficulty


def _estimate_difficulty(query_lower: str, task_type: str) -> str:
    """난이도를 판단합니다."""
    high_score = sum(1 for kw in DIFFICULTY_KEYWORDS["high"] if kw in query_lower)
    medium_score = sum(1 for kw in DIFFICULTY_KEYWORDS["medium"] if kw in query_lower)
    low_score = sum(1 for kw in DIFFICULTY_KEYWORDS["low"] if kw in query_lower)

    # 입력 길이 기반 보정
    if len(query_lower) > 200:
        high_score += 1
    elif len(query_lower) > 100:
        medium_score += 1

    # 작업 유형 기반 보정
    if task_type in ("reasoning", "sensitive"):
        high_score += 1
    elif task_type in ("coding", "planning"):
        medium_score += 1
    elif task_type in ("simple_qa", "summarize", "translate", "writing_edit"):
        low_score += 1

    if high_score > medium_score and high_score > low_score:
        return "high"
    elif medium_score > low_score:
        return "medium"
    return "low"


# ─── LangChain Runnable 인터페이스 ──────────────────────────────
# 향후 LLM 기반 분류기로 교체할 때 이 Runnable을 사용합니다.

def _classify_runnable_fn(inputs: dict) -> dict:
    """LangChain Runnable 호환 함수"""
    query = inputs["query"]
    task_type, difficulty = classify_task(query)
    return {
        "query": query,
        "task_type": task_type,
        "difficulty": difficulty,
    }


# LangChain Runnable로 래핑 — chain 조합 시 사용 가능
task_classifier_runnable = RunnableLambda(_classify_runnable_fn)
