import json
import os
import time
from typing import Any, Dict, Tuple

REGION = os.getenv("AWS_REGION", "us-east-1")
USE_BEDROCK = os.getenv("USE_BEDROCK", "true").lower() == "true"
BEDROCK_FALLBACK_MODEL_ID = os.getenv(
    "BEDROCK_FALLBACK_MODEL_ID",
    "anthropic.claude-opus-4-8",
)
BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "256"))


MODEL_CATALOG = {
    "gemma-4-e2b": {
        "display_name": "Gemma 4 E2B",
        "provider": "google",
        "input_cost_per_1m": 0.04,
        "output_cost_per_1m": 0.08,
        "co2_mg_per_token": 0.120,
        "quality": 0.45,
        "speed": 0.95,
        "cost": 0.98,
        "carbon": 0.98,
        "best_for": ["simple_qa", "translate", "summarize", "writing_edit"],
        "bedrock_model_id": "google.gemma-4-e2b",
    },
    "gemma-4-26b-a4b": {
        "display_name": "Gemma 4 26B-A4B",
        "provider": "google",
        "input_cost_per_1m": 0.13,
        "output_cost_per_1m": 0.40,
        "co2_mg_per_token": 0.180,
        "quality": 0.62,
        "speed": 0.80,
        "cost": 0.92,
        "carbon": 0.94,
        "best_for": ["simple_qa", "summarize", "translate", "writing_edit", "coding"],
        "bedrock_model_id": "google.gemma-4-26b-a4b",
    },
    "gpt-5.5": {
        "display_name": "GPT-5.5",
        "provider": "openai",
        "input_cost_per_1m": 5.50,
        "output_cost_per_1m": 33.00,
        "co2_mg_per_token": 0.699,
        "quality": 0.94,
        "speed": 0.55,
        "cost": 0.18,
        "carbon": 0.45,
        "best_for": ["coding", "reasoning", "planning", "sensitive"],
        "bedrock_model_id": "openai.gpt-5-5",
    },
    "claude-opus": {
        "display_name": "Claude Opus 4.8",
        "provider": "anthropic",
        "input_cost_per_1m": 5.00,
        "output_cost_per_1m": 25.00,
        "co2_mg_per_token": 0.872,
        "quality": 0.98,
        "speed": 0.45,
        "cost": 0.15,
        "carbon": 0.30,
        "best_for": ["reasoning", "coding", "planning", "sensitive"],
        "bedrock_model_id": "anthropic.claude-opus-4-8",
    },
}

BASELINE_MODEL = "claude-opus"

POLICY_WEIGHTS = {
    "cost_first": {"quality": 0.15, "cost": 0.45, "carbon": 0.25, "speed": 0.15},
    "carbon_first": {"quality": 0.15, "cost": 0.20, "carbon": 0.50, "speed": 0.15},
    "quality_first": {"quality": 0.55, "cost": 0.10, "carbon": 0.10, "speed": 0.25},
    "balanced": {"quality": 0.30, "cost": 0.25, "carbon": 0.25, "speed": 0.20},
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return respond(200, {"ok": True})

    try:
        body = parse_body(event)
        query = str(body.get("query", "")).strip()
        if not query:
            return respond(400, {"error": "query is required"})

        policy = body.get("policy", "balanced")
        if policy not in POLICY_WEIGHTS:
            policy = "balanced"

        baseline_model = body.get("baseline_model", BASELINE_MODEL)
        if baseline_model not in MODEL_CATALOG:
            baseline_model = BASELINE_MODEL

        task_type, difficulty = classify_task(query)
        selected_model, reason, alternatives = select_model(task_type, difficulty, policy)
        input_tokens, output_tokens = estimate_tokens(query, task_type, difficulty)
        savings = calculate_savings(
            selected_model,
            baseline_model,
            input_tokens,
            output_tokens,
        )

        started = time.perf_counter()
        llm_answer, bedrock_model_id, is_bedrock = generate_answer(
            selected_model=selected_model,
            query=query,
            task_type=task_type,
            difficulty=difficulty,
            max_tokens=min(output_tokens, BEDROCK_MAX_TOKENS),
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        payload = {
            "query": query,
            "task_type": task_type,
            "difficulty": difficulty,
            "policy": policy,
            "baseline_model": baseline_model,
            "selected_model": selected_model,
            "selected_display_name": MODEL_CATALOG[selected_model]["display_name"],
            "bedrock_model_id": bedrock_model_id,
            "reason": reason,
            "estimated_tokens": savings["estimated_tokens"],
            "cost": savings["cost"],
            "carbon": savings["carbon"],
            "alternatives": alternatives,
            "answer": llm_answer,
            "is_bedrock": is_bedrock,
            "latency_ms": latency_ms,
        }
        return respond(200, payload)
    except Exception as exc:
        return respond(500, {"error": str(exc), "type": exc.__class__.__name__})


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    if "body" not in event:
        return event if isinstance(event, dict) else {}
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")
    if isinstance(body, str):
        return json.loads(body or "{}")
    return body


def respond(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "content-type,authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def classify_task(query: str) -> Tuple[str, str]:
    text = query.lower()
    if any(word in text for word in ["코드", "버그", "함수", "api", "python", "react", "debug", "code"]):
        task_type = "coding"
    elif any(word in text for word in ["설계", "분석", "비교", "전략", "architecture", "reason"]):
        task_type = "reasoning"
    elif any(word in text for word in ["요약", "정리", "summarize", "summary"]):
        task_type = "summarize"
    elif any(word in text for word in ["번역", "translate", "영어", "한국어"]):
        task_type = "translate"
    elif any(word in text for word in ["이메일", "문장", "고쳐", "수정", "rewrite", "edit"]):
        task_type = "writing_edit"
    elif any(word in text for word in ["기획", "아이디어", "발표", "제안", "planning"]):
        task_type = "planning"
    elif any(word in text for word in ["법률", "의료", "금융", "보안", "계약", "개인정보"]):
        task_type = "sensitive"
    else:
        task_type = "simple_qa"

    if len(query) > 220 or task_type in ["reasoning", "sensitive"]:
        difficulty = "high"
    elif len(query) > 100 or task_type in ["coding", "planning"]:
        difficulty = "medium"
    else:
        difficulty = "low"

    return task_type, difficulty


def select_model(task_type: str, difficulty: str, policy: str) -> Tuple[str, str, list]:
    weights = POLICY_WEIGHTS[policy]
    min_quality = {"low": 0.0, "medium": 0.55, "high": 0.80}[difficulty]

    scored = []
    for model_id, spec in MODEL_CATALOG.items():
        if spec["quality"] < min_quality:
            continue
        task_fit = 0.15 if task_type in spec["best_for"] else 0.0
        score = (
            spec["quality"] * weights["quality"]
            + spec["cost"] * weights["cost"]
            + spec["carbon"] * weights["carbon"]
            + spec["speed"] * weights["speed"]
            + task_fit
        )
        scored.append((model_id, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    selected = scored[0][0] if scored else BASELINE_MODEL
    alternatives = [model_id for model_id, _ in scored[1:3]]

    reason = build_reason(selected, task_type, difficulty, policy)
    return selected, reason, alternatives


def build_reason(selected_model: str, task_type: str, difficulty: str, policy: str) -> str:
    display_name = MODEL_CATALOG[selected_model]["display_name"]
    return (
        f"{task_type} 작업이며 난이도는 {difficulty}로 판단했습니다. "
        f"{policy} 정책 기준에서 비용, 탄소, 품질 점수의 균형이 가장 좋아 "
        f"{display_name} 모델을 선택했습니다."
    )


def estimate_tokens(query: str, task_type: str, difficulty: str) -> Tuple[int, int]:
    input_tokens = max(len(query) * 2, 20)
    output_map = {
        "simple_qa": {"low": 120, "medium": 250, "high": 500},
        "summarize": {"low": 160, "medium": 320, "high": 700},
        "translate": {"low": 120, "medium": 250, "high": 500},
        "writing_edit": {"low": 120, "medium": 220, "high": 450},
        "coding": {"low": 250, "medium": 600, "high": 1200},
        "reasoning": {"low": 300, "medium": 800, "high": 1500},
        "planning": {"low": 300, "medium": 650, "high": 1200},
        "sensitive": {"low": 250, "medium": 500, "high": 900},
    }
    output_tokens = output_map.get(task_type, {}).get(difficulty, 250)
    return input_tokens, output_tokens


def calculate_savings(
    selected_model_id: str,
    baseline_model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> Dict[str, Any]:
    total_tokens = input_tokens + output_tokens
    selected_cost = calculate_cost(selected_model_id, input_tokens, output_tokens)
    baseline_cost = calculate_cost(baseline_model_id, input_tokens, output_tokens)
    selected_co2 = calculate_co2(selected_model_id, total_tokens)
    baseline_co2 = calculate_co2(baseline_model_id, total_tokens)

    saved_cost = max(baseline_cost - selected_cost, 0.0)
    saved_co2 = max(baseline_co2 - selected_co2, 0.0)
    return {
        "estimated_tokens": {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens,
        },
        "cost": {
            "selected_usd": round(selected_cost, 6),
            "baseline_usd": round(baseline_cost, 6),
            "saved_usd": round(saved_cost, 6),
            "percent_cheaper": round(saved_cost / baseline_cost * 100, 1)
            if baseline_cost
            else 0.0,
        },
        "carbon": {
            "selected_g": round(selected_co2, 6),
            "baseline_g": round(baseline_co2, 6),
            "saved_g": round(saved_co2, 6),
            "percent_less_co2": round(saved_co2 / baseline_co2 * 100, 1)
            if baseline_co2
            else 0.0,
        },
    }


def calculate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    spec = MODEL_CATALOG[model_id]
    return (
        input_tokens / 1_000_000 * spec["input_cost_per_1m"]
        + output_tokens / 1_000_000 * spec["output_cost_per_1m"]
    )


def calculate_co2(model_id: str, total_tokens: int) -> float:
    return total_tokens * MODEL_CATALOG[model_id]["co2_mg_per_token"] / 1000


def generate_answer(
    selected_model: str,
    query: str,
    task_type: str,
    difficulty: str,
    max_tokens: int,
) -> Tuple[str, str, bool]:
    model_id = MODEL_CATALOG[selected_model].get("bedrock_model_id") or BEDROCK_FALLBACK_MODEL_ID
    if not USE_BEDROCK:
        return (
            f"[mock] {selected_model} 모델로 처리할 수 있는 요청입니다: {query}",
            model_id,
            False,
        )

    system_prompt = (
        "You are ECOROUTE, an AI model routing assistant. "
        "Answer concisely in Korean. "
        "The router has already selected the model for this request. "
        f"Task type: {task_type}. Difficulty: {difficulty}."
    )

    import boto3

    client = boto3.client("bedrock-runtime", region_name=REGION)
    try:
        response = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": query}],
                }
            ],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": 0.3,
            },
        )
    except Exception:
        if model_id == BEDROCK_FALLBACK_MODEL_ID:
            raise
        model_id = BEDROCK_FALLBACK_MODEL_ID
        response = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": query}],
                }
            ],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": 0.3,
            },
        )

    text = response["output"]["message"]["content"][0]["text"]
    return text, model_id, True
