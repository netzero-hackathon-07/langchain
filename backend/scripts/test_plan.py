"""ECOCACHE 멀티스텝 플랜 테스트 스크립트

복합 요청을 서브태스크로 분해하고, 각 스텝별 최적 모델을 배정하여
전체 절감량을 시뮬레이션합니다.

실행:
    # 서버 실행 후
    python scripts/test_plan.py

    # 서버 없이 내부 로직만
    python scripts/test_plan.py --offline
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PLAN_EXAMPLES = [
    {
        "description": "자료 검색 + 코딩 + 보고서",
        "query": "최신 AI 트렌드 자료를 찾아서 정리하고, Python으로 데이터 시각화 코드를 구현한 다음, 보고서로 만들어줘",
        "policy": "balanced",
    },
    {
        "description": "설계 + 코딩 + 테스트",
        "query": "마이크로서비스 아키텍처를 설계하고, FastAPI로 API 서버를 구현하고, 테스트 코드도 작성해줘",
        "policy": "quality_first",
    },
    {
        "description": "리서치 + 분석 + 기획 + 문서",
        "query": "경쟁사 AI 서비스를 조사하고 비교 분석해서, 우리 서비스 차별화 전략을 기획하고, 제안서로 작성해줘",
        "policy": "carbon_first",
    },
    {
        "description": "번역 + 요약 + 교정",
        "query": "이 영어 논문을 한국어로 번역하고, 핵심 내용을 요약한 다음, 문장을 자연스럽게 다듬어줘",
        "policy": "cost_first",
    },
    {
        "description": "단일 작업 (분해 불필요)",
        "query": "Python에서 list comprehension 사용법을 알려줘",
        "policy": "balanced",
    },
]


def test_offline():
    """서버 없이 내부 로직 테스트"""
    from router.plan_executor import execute_plan
    from llm.mock_client import MockLLMClient

    client = MockLLMClient()

    print("=" * 75)
    print("  ECOCACHE - 멀티스텝 플랜 시뮬레이션 (Offline)")
    print("=" * 75)

    for i, example in enumerate(PLAN_EXAMPLES, 1):
        result = execute_plan(
            query=example["query"],
            policy=example["policy"],
            llm_client=client,
        )

        print(f"\n{'━' * 75}")
        print(f"  [{i}] {example['description']}")
        print(f"  Query: {example['query'][:70]}...")
        print(f"  Policy: {example['policy']}")
        print(f"  Multi-step: {'예' if result.is_multi_step else '아니오'} ({result.total_steps}스텝)")
        print(f"{'─' * 75}")

        # 각 스텝 출력
        for step in result.steps:
            saved_pct = round((step.saved_cost_usd / step.baseline_cost_usd) * 100, 1) if step.baseline_cost_usd > 0 else 0
            co2_pct = round((step.saved_co2_g / step.baseline_co2_g) * 100, 1) if step.baseline_co2_g > 0 else 0
            print(f"  Step {step.step}: {step.action}")
            print(f"         모델: {step.selected_model} ({step.task_type}, {step.difficulty})")
            print(f"         토큰: {step.total_tokens} | 비용: ${step.cost_usd:.5f} (↓{saved_pct}%) | CO₂: {step.co2_g:.5f}g (↓{co2_pct}%)")

        # 합산
        print(f"{'─' * 75}")
        print(f"  📊 총합 결과:")
        print(f"     총 토큰: {result.total_tokens}")
        print(f"     총 비용: ${result.total_cost_usd:.6f} (baseline: ${result.baseline_total_cost_usd:.6f})")
        print(f"     총 CO₂: {result.total_co2_g:.6f}g (baseline: ${result.baseline_total_co2_g:.6f}g)")
        print(f"     💰 비용 절감: ${result.saved_cost_usd:.6f} (-{result.percent_cheaper}%)")
        print(f"     🌍 CO₂ 절감: {result.saved_co2_g:.6f}g (-{result.percent_less_co2}%)")
        print(f"     🤖 모델 배정:")
        for model, actions in result.model_assignment.items():
            print(f"        {model}: {', '.join(actions)}")

    print(f"\n{'━' * 75}")
    print(f"  총 {len(PLAN_EXAMPLES)}개 시나리오 시뮬레이션 완료")
    print(f"{'━' * 75}\n")


def test_online():
    """서버에 HTTP 요청으로 테스트"""
    try:
        import httpx
    except ImportError:
        print("httpx 필요: pip install httpx")
        sys.exit(1)

    BASE_URL = "http://localhost:8000"

    try:
        r = httpx.get(f"{BASE_URL}/")
        print(f"서버 상태: {r.json()}\n")
    except httpx.ConnectError:
        print("서버에 연결할 수 없습니다.")
        print("  uvicorn main:app --reload")
        print("  python scripts/test_plan.py --offline")
        sys.exit(1)

    print("=" * 75)
    print("  ECOCACHE - 멀티스텝 플랜 시뮬레이션 (POST /plan)")
    print("=" * 75)

    for i, example in enumerate(PLAN_EXAMPLES, 1):
        r = httpx.post(f"{BASE_URL}/plan", json={
            "query": example["query"],
            "policy": example["policy"],
        })
        data = r.json()

        print(f"\n{'━' * 75}")
        print(f"  [{i}] {example['description']}")
        print(f"  Multi-step: {'예' if data['is_multi_step'] else '아니오'} ({data['total_steps']}스텝)")

        for step in data["steps"]:
            print(f"  Step {step['step']}: {step['action']} → {step['selected_model']} ({step['task_type']})")

        print(f"  💰 비용: ${data['total_cost_usd']:.6f} → 절감 ${data['saved_cost_usd']:.6f} (-{data['percent_cheaper']}%)")
        print(f"  🌍 CO₂: {data['total_co2_g']:.6f}g → 절감 {data['saved_co2_g']:.6f}g (-{data['percent_less_co2']}%)")

    # 전체 JSON 하나 출력
    print(f"\n{'━' * 75}")
    print("\n📋 응답 JSON 전체 예시:")
    r = httpx.post(f"{BASE_URL}/plan", json={
        "query": PLAN_EXAMPLES[0]["query"],
        "policy": PLAN_EXAMPLES[0]["policy"],
    })
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if "--offline" in sys.argv:
        test_offline()
    else:
        test_online()
