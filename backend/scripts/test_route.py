"""ECOCACHE 테스트 스크립트

서버를 실행한 후 이 스크립트로 POST /route 엔드포인트를 테스트합니다.

실행:
    1. uvicorn main:app --reload
    2. python scripts/test_route.py

또는 서버 없이 내부 로직만 테스트:
    python scripts/test_route.py --offline
"""

import json
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_offline():
    """서버 없이 내부 로직만 테스트"""
    from router.task_classifier import classify_task
    from router.model_selector import select_model
    from router.carbon_estimator import estimate_tokens, calculate_savings

    # 예시 로드
    examples_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples",
        "route_examples.json",
    )
    with open(examples_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    print("=" * 70)
    print("  ECOCACHE - Offline 테스트 (서버 없이 내부 로직 검증)")
    print("=" * 70)

    for i, example in enumerate(examples, 1):
        query = example["query"]
        policy = example["policy"]
        expected_type = example.get("expected_task_type", "?")
        desc = example.get("description", "")

        # 분류
        task_type, difficulty = classify_task(query)
        # 모델 선택
        selected, reason, alternatives = select_model(task_type, difficulty, policy)
        # 토큰/절감량
        inp, out = estimate_tokens(query, task_type, difficulty)
        savings = calculate_savings(selected, "claude-sonnet", inp, out)

        # 결과 출력
        type_match = "✓" if task_type == expected_type else "✗"
        print(f"\n{'─' * 70}")
        print(f"  [{i}] {desc}")
        print(f"  Query: {query[:60]}{'...' if len(query) > 60 else ''}")
        print(f"  Policy: {policy}")
        print(f"  Task Type: {task_type} (expected: {expected_type}) {type_match}")
        print(f"  Difficulty: {difficulty}")
        print(f"  Selected Model: {selected}")
        print(f"  Alternatives: {', '.join(alternatives)}")
        print(f"  Tokens: {savings['estimated_tokens']['total']} (in:{inp} + out:{out})")
        print(f"  Cost Saved: ${savings['cost']['saved_usd']:.6f} (-{savings['cost']['percent_cheaper']}%)")
        print(f"  CO₂ Saved: {savings['carbon']['saved_g']:.6f}g (-{savings['carbon']['percent_less_co2']}%)")
        print(f"  Reason: {reason[:80]}...")

    print(f"\n{'═' * 70}")
    print(f"  총 {len(examples)}개 예시 테스트 완료")
    print(f"{'═' * 70}\n")


def test_online():
    """서버에 HTTP 요청을 보내 테스트"""
    try:
        import httpx
    except ImportError:
        print("httpx가 필요합니다: pip install httpx")
        sys.exit(1)

    BASE_URL = "http://localhost:8000"

    # 서버 상태 확인
    try:
        r = httpx.get(f"{BASE_URL}/")
        if r.status_code != 200:
            print(f"서버 응답 오류: {r.status_code}")
            sys.exit(1)
        print(f"서버 상태: {r.json()}\n")
    except httpx.ConnectError:
        print("서버에 연결할 수 없습니다. 먼저 서버를 실행하세요:")
        print("  uvicorn main:app --reload")
        print("\n서버 없이 테스트하려면:")
        print("  python scripts/test_route.py --offline")
        sys.exit(1)

    # 예시 로드
    examples_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples",
        "route_examples.json",
    )
    with open(examples_path, "r", encoding="utf-8") as f:
        examples = json.load(f)

    print("=" * 70)
    print("  ECOCACHE - Online 테스트 (POST /route)")
    print("=" * 70)

    for i, example in enumerate(examples, 1):
        payload = {
            "query": example["query"],
            "policy": example["policy"],
            "baseline_model": "claude-sonnet",
        }
        r = httpx.post(f"{BASE_URL}/route", json=payload)
        data = r.json()

        desc = example.get("description", "")
        print(f"\n{'─' * 70}")
        print(f"  [{i}] {desc}")
        print(f"  Query: {data['query'][:60]}...")
        print(f"  Task Type: {data['task_type']} | Difficulty: {data['difficulty']}")
        print(f"  Selected: {data['selected_model']}")
        print(f"  Alternatives: {', '.join(data['alternatives'])}")
        print(f"  Cost: ${data['cost']['selected_usd']:.6f} (saved ${data['cost']['saved_usd']:.6f}, -{data['cost']['percent_cheaper']}%)")
        print(f"  CO₂: {data['carbon']['selected_g']:.6f}g (saved {data['carbon']['saved_g']:.6f}g, -{data['carbon']['percent_less_co2']}%)")
        print(f"  Reason: {data['reason'][:80]}...")
        print(f"  Mock Answer: {data['mock_answer'][:60]}...")

    print(f"\n{'═' * 70}")
    print(f"  총 {len(examples)}개 요청 테스트 완료")
    print(f"{'═' * 70}\n")

    # 전체 JSON 예시 하나 출력
    print("\n📋 응답 JSON 전체 예시 (첫 번째 요청):")
    r = httpx.post(
        f"{BASE_URL}/route",
        json={"query": examples[0]["query"], "policy": examples[0]["policy"]},
    )
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if "--offline" in sys.argv:
        test_offline()
    else:
        test_online()
