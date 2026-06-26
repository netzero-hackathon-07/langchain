"""ECOCACHE 실제 AI 테스트"""
import httpx, json, sys

BASE = "http://localhost:8000"
query = sys.argv[1] if len(sys.argv) > 1 else "Python으로 피보나치 함수를 구현하고, 사용법을 설명해줘"
policy = sys.argv[2] if len(sys.argv) > 2 else "balanced"

print(f"\n요청: {query}")
print(f"정책: {policy}")
print("Claude Haiku 호출 중...\n")

r = httpx.post(f"{BASE}/plan", json={"query": query, "policy": policy}, timeout=60)
data = r.json()

if r.status_code != 200:
    print(f"에러: {data}")
    sys.exit(1)

print(f"멀티스텝: {'예' if data['is_multi_step'] else '아니오'} ({data['total_steps']}스텝)")
print("=" * 60)

for step in data["steps"]:
    print(f"\nStep {step['step']}: {step['action']}")
    print(f"  추천 모델: {step['selected_model']} ({step['task_type']}, {step['difficulty']})")
    print(f"  이유: {step['reason']}")
    print(f"  토큰: {step['total_tokens']} (in:{step['input_tokens']} + out:{step['output_tokens']})")
    print(f"  AI 응답:")
    # 응답 첫 200자만
    answer = step["mock_answer"][:300]
    print(f"  {answer}{'...' if len(step['mock_answer']) > 300 else ''}")

print("\n" + "=" * 60)
print(f"총 토큰: {data['total_tokens']}")
print(f"비용: ${data['total_cost_usd']:.6f} (baseline: ${data['baseline_total_cost_usd']:.6f})")
print(f"CO2: {data['total_co2_g']:.6f}g (baseline: {data['baseline_total_co2_g']:.6f}g)")
print(f"절감: -{data['percent_cheaper']}% 비용, -{data['percent_less_co2']}% CO2")
print(f"\n모델 배정: {json.dumps(data['model_assignment'], ensure_ascii=False)}")

# 사용량 확인
u = httpx.get(f"{BASE}/usage").json()
print(f"\n[사용량] 총 ${u['total_cost_usd']:.4f} / ${u['budget_limit_usd']} (잔여: ${u['budget_remaining_usd']:.4f})")
