"""ECOCACHE Backend - AI Model Routing Engine

Claude 3.5 Haiku가 직접:
1. 사용자 요청을 분석/분해
2. 각 서브태스크에 최적 모델 추천
3. 각 스텝을 실제로 수행

실행:
    uvicorn main:app --reload

Swagger:
    http://localhost:8000/docs
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from schemas.route_response import (
    HealthResponse,
    PlanRequest,
    PlanResponse,
    StepDetail,
)
from schemas.graph_response import (
    PipelineGraphResponse,
    PipelineNode,
    PipelineEdge,
    PipelineSummary,
    NodePosition,
)
from router.llm_classifier import classify_and_decompose
from router.carbon_estimator import calculate_cost, calculate_co2
from router.model_catalog import get_all_models, get_model, BASELINE_MODEL_ID
from router.routing_policy import get_all_policies
from llm.anthropic_client import AnthropicLLMClient


# ─── API Key & Client ───────────────────────────────────────────

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY가 .env에 설정되지 않았습니다.")

llm_client = AnthropicLLMClient(api_key=ANTHROPIC_API_KEY)
print("[ECOCACHE] Claude Haiku 4.5 연결됨 - 실제 AI 모드")


# ─── Usage Tracking ($5 한도) ───────────────────────────────────

usage_tracker = {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "total_cost_usd": 0.0,
    "request_count": 0,
}
BUDGET_LIMIT_USD = 5.0

# Haiku 4.5 가격
HAIKU_INPUT_PER_1M = 1.00
HAIKU_OUTPUT_PER_1M = 5.00


def track_usage(input_tokens: int, output_tokens: int):
    """토큰 사용량 추적"""
    cost = (input_tokens / 1_000_000) * HAIKU_INPUT_PER_1M + \
           (output_tokens / 1_000_000) * HAIKU_OUTPUT_PER_1M
    usage_tracker["total_input_tokens"] += input_tokens
    usage_tracker["total_output_tokens"] += output_tokens
    usage_tracker["total_cost_usd"] += cost
    usage_tracker["request_count"] += 1


def check_budget():
    """예산 초과 확인"""
    if usage_tracker["total_cost_usd"] >= BUDGET_LIMIT_USD:
        raise HTTPException(
            status_code=429,
            detail=f"예산 한도 ${BUDGET_LIMIT_USD} 초과. 현재 사용: ${usage_tracker['total_cost_usd']:.4f}"
        )


# ─── FastAPI App ────────────────────────────────────────────────

app = FastAPI(
    title="ECOCACHE - AI Model Routing Engine",
    description="Claude 3.5 Haiku가 요청을 분석/분해하고, 각 스텝에 최적 모델을 추천하는 라우팅 엔진",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ──────────────────────────────────────────────────

@app.get("/", response_model=HealthResponse)
def health_check():
    return HealthResponse(service="ECOCACHE", status="online", version="1.0.0")


@app.get("/usage")
def get_usage():
    """현재 API 사용량 조회"""
    return {
        **usage_tracker,
        "budget_limit_usd": BUDGET_LIMIT_USD,
        "budget_remaining_usd": round(BUDGET_LIMIT_USD - usage_tracker["total_cost_usd"], 4),
    }


@app.post("/plan", response_model=PlanResponse)
def plan_and_execute(request: PlanRequest):
    """
    핵심 API: Claude Haiku가 요청을 분해하고, 각 스텝에 모델 추천 + 실제 수행.

    흐름:
    1. Haiku가 요청 분석 → 서브태스크 분해 + 모델 추천
    2. 각 스텝을 Haiku가 실제로 수행 (추천 모델 역할)
    3. 비용/CO₂ 절감량 계산 (실측 토큰 기반)
    """
    check_budget()

    query = request.query
    policy = request.policy
    baseline_model = request.baseline_model

    # ─── Step 1: LLM이 분해 + 추천 ───
    classification = classify_and_decompose(query, policy, llm_client)
    subtasks = classification.get("subtasks", [])

    if not subtasks:
        raise HTTPException(status_code=500, detail="작업 분해 실패")

    # 분류 호출 토큰도 사용량에 추적
    track_usage(
        classification.get("_classifier_input_tokens", 0),
        classification.get("_classifier_output_tokens", 0),
    )

    # ─── Step 2: 각 스텝 실제 수행 ───
    steps = []
    total_input = 0
    total_output = 0

    valid_models = set(get_all_models().keys())

    for subtask in subtasks:
        step_num = subtask["step"]
        action = subtask["action"]
        task_type = subtask.get("task_type", "simple_qa")
        difficulty = subtask.get("difficulty", "medium")
        recommended_model = subtask.get("recommended_model", "claude-haiku")
        reason = subtask.get("reason", "")

        # LLM이 카탈로그에 없는 모델을 추천하면 fallback
        if recommended_model not in valid_models:
            recommended_model = "gemini-flash"

        # 각 스텝을 실제로 수행
        step_prompt = f"""작업: {action}

원본 요청의 맥락: "{query}"

이 단계를 수행해줘. 결과만 간결하게 출력해."""

        step_response = llm_client.generate(
            model_id=recommended_model,
            prompt=step_prompt,
            max_tokens=800,
            temperature=0.7,
        )

        # 토큰 추적
        track_usage(step_response.input_tokens, step_response.output_tokens)
        total_input += step_response.input_tokens
        total_output += step_response.output_tokens

        # 비용/CO₂ 계산 (추천 모델 기준 vs baseline)
        step_total_tokens = step_response.input_tokens + step_response.output_tokens
        selected_cost = calculate_cost(recommended_model, step_response.input_tokens, step_response.output_tokens)
        baseline_cost = calculate_cost(baseline_model, step_response.input_tokens, step_response.output_tokens)
        selected_co2 = calculate_co2(recommended_model, step_total_tokens)
        baseline_co2 = calculate_co2(baseline_model, step_total_tokens)

        steps.append(StepDetail(
            step=step_num,
            action=action,
            task_type=task_type,
            difficulty=difficulty,
            selected_model=recommended_model,
            reason=reason,
            alternatives=[],
            input_tokens=step_response.input_tokens,
            output_tokens=step_response.output_tokens,
            total_tokens=step_total_tokens,
            cost_usd=round(selected_cost, 6),
            co2_g=round(selected_co2, 6),
            baseline_cost_usd=round(baseline_cost, 6),
            baseline_co2_g=round(baseline_co2, 6),
            saved_cost_usd=round(max(baseline_cost - selected_cost, 0), 6),
            saved_co2_g=round(max(baseline_co2 - selected_co2, 0), 6),
            answer=step_response.content,
        ))

    # ─── Step 3: 합산 ───
    total_tokens = total_input + total_output
    total_cost = sum(s.cost_usd for s in steps)
    total_co2 = sum(s.co2_g for s in steps)
    baseline_total_cost = sum(s.baseline_cost_usd for s in steps)
    baseline_total_co2 = sum(s.baseline_co2_g for s in steps)
    saved_cost = baseline_total_cost - total_cost
    saved_co2 = baseline_total_co2 - total_co2
    pct_cheaper = round((saved_cost / baseline_total_cost) * 100, 1) if baseline_total_cost > 0 else 0.0
    pct_less_co2 = round((saved_co2 / baseline_total_co2) * 100, 1) if baseline_total_co2 > 0 else 0.0

    # 모델 배정 요약
    model_assignment = {}
    for s in steps:
        if s.selected_model not in model_assignment:
            model_assignment[s.selected_model] = []
        model_assignment[s.selected_model].append(s.action)

    return PlanResponse(
        query=query,
        policy=policy,
        baseline_model=baseline_model,
        is_multi_step=len(steps) > 1,
        total_steps=len(steps),
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


@app.post("/plan/graph", response_model=PipelineGraphResponse)
def plan_as_graph(request: PlanRequest):
    """멀티스텝 결과를 노드-엣지 그래프로 반환"""
    import uuid
    from datetime import datetime, timezone

    # /plan 로직 재사용
    plan_result = plan_and_execute(request)

    pipeline_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    ROLE_MAP = {
        "summarize": "searcher", "simple_qa": "searcher",
        "translate": "translator", "writing_edit": "writer",
        "coding": "coder", "reasoning": "analyst",
        "planning": "planner", "sensitive": "reviewer",
    }

    nodes = []
    for step in plan_result.steps:
        node_id = f"node-{step.step:03d}"
        role = ROLE_MAP.get(step.task_type, "executor")
        nodes.append(PipelineNode(
            id=node_id, role=role, model=step.selected_model,
            label=step.action, task_type=step.task_type, difficulty=step.difficulty,
            estimated_input_tokens=step.input_tokens,
            estimated_output_tokens=step.output_tokens,
            system_prompt_tokens=150, call_count=1,
            cost_usd=step.cost_usd, co2_g=step.co2_g,
            baseline_cost_usd=step.baseline_cost_usd, baseline_co2_g=step.baseline_co2_g,
            reason=step.reason, alternatives=step.alternatives,
            position=NodePosition(x=100 + (step.step - 1) * 300, y=200),
            answer=step.answer,
        ))

    edges = []
    for i in range(len(nodes) - 1):
        transfer = "context_pass" if nodes[i].task_type != nodes[i+1].task_type else "result_only"
        edges.append(PipelineEdge(
            id=f"edge-{i+1:03d}",
            source_node_id=nodes[i].id, target_node_id=nodes[i+1].id,
            data_transfer=transfer,
            token_overhead=200 if transfer == "context_pass" else 100,
        ))

    actions = [s.action for s in plan_result.steps]
    name = " → ".join(actions) if len(actions) <= 3 else f"{actions[0]} → ... → {actions[-1]} ({len(actions)}스텝)"

    summary = PipelineSummary(
        total_nodes=plan_result.total_steps, total_tokens=plan_result.total_tokens,
        total_cost_usd=plan_result.total_cost_usd, total_co2_g=plan_result.total_co2_g,
        baseline_total_cost_usd=plan_result.baseline_total_cost_usd,
        baseline_total_co2_g=plan_result.baseline_total_co2_g,
        saved_cost_usd=plan_result.saved_cost_usd, saved_co2_g=plan_result.saved_co2_g,
        percent_cheaper=plan_result.percent_cheaper, percent_less_co2=plan_result.percent_less_co2,
        model_assignment=plan_result.model_assignment,
    )

    return PipelineGraphResponse(
        id=pipeline_id, name=name, query=request.query,
        policy=request.policy, baseline_model=request.baseline_model,
        created_at=now, updated_at=now,
        nodes=nodes, edges=edges, summary=summary,
    )


@app.get("/models")
def list_models():
    """모델 카탈로그 조회"""
    catalog = get_all_models()
    return {
        model_id: {
            "model_id": spec.model_id, "display_name": spec.display_name,
            "provider": spec.provider, "co2_mg_per_token": spec.co2_mg_per_token,
            "quality_score": spec.quality_score, "best_for": spec.best_for,
        }
        for model_id, spec in catalog.items()
    }


@app.get("/policies")
def list_policies():
    """운영 정책 목록 조회"""
    policies = get_all_policies()
    return {
        name: {"label": pw.label, "description": pw.description}
        for name, pw in policies.items()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
