"""ECOCACHE 라이브 데모 - 실제 요청 → 분해 → 배정 → 절감 계산"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

# 테스트 쿼리 (직접 바꿔가면서 테스트 가능)
query = sys.argv[1] if len(sys.argv) > 1 else (
    "AWS 클라우드 아키텍처 자료를 조사해서 정리하고, "
    "Python FastAPI로 API 서버를 코딩하고, "
    "최종 보고서로 작성해줘"
)
policy = sys.argv[2] if len(sys.argv) > 2 else "balanced"

try:
    r = httpx.post(f"{BASE_URL}/plan", json={"query": query, "policy": policy})
except httpx.ConnectError:
    print("서버가 꺼져있습니다. 먼저: uvicorn main:app --reload")
    sys.exit(1)

data = r.json()

print()
print("=" * 65)
print("  ECOCACHE - 멀티스텝 시뮬레이션 결과")
print("=" * 65)
print(f"  입력: {data['query']}")
print(f"  정책: {data['policy']}")
print(f"  기준 모델: {data['baseline_model']}")
print(f"  멀티스텝: {'예' if data['is_multi_step'] else '아니오'} ({data['total_steps']}스텝)")
print("-" * 65)
print()
print("  [작업 분해 + 모델 배정]")
print()

for step in data["steps"]:
    print(f"  Step {step['step']}: {step['action']}")
    print(f"         배정 모델: {step['selected_model']}")
    print(f"         작업유형: {step['task_type']} | 난이도: {step['difficulty']}")
    print(f"         토큰: {step['total_tokens']} | 비용: ${step['cost_usd']:.5f} | CO2: {step['co2_g']:.5f}g")
    baseline_label = f"${step['baseline_cost_usd']:.5f} / {step['baseline_co2_g']:.5f}g"
    print(f"         (baseline 단일모델이면: {baseline_label})")
    print()

print("-" * 65)
print("  [총합 비교]")
print()
print(f"  {'구분':<12} | {'ECOCACHE (최적배정)':<20} | {'Baseline (단일모델)':<20}")
print(f"  {'-'*12}-|-{'-'*20}-|-{'-'*20}")
print(f"  {'총 토큰':<12} | {data['total_tokens']:<20} | {'(동일)':<20}")
print(f"  {'총 비용':<12} | ${data['total_cost_usd']:<19.6f} | ${data['baseline_total_cost_usd']:<19.6f}")
print(f"  {'총 CO2':<12} | {data['total_co2_g']:<18.6f}g | {data['baseline_total_co2_g']:<18.6f}g")
print()
print(f"  ==> 비용 절감: ${data['saved_cost_usd']:.6f} (-{data['percent_cheaper']}%)")
print(f"  ==> CO2 절감: {data['saved_co2_g']:.6f}g (-{data['percent_less_co2']}%)")
print()
print("  [모델 배정표]")
for model, actions in data["model_assignment"].items():
    print(f"    {model}: {' / '.join(actions)}")

print()
print("=" * 65)
print()
