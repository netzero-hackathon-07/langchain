# ECOCACHE Backend - AI Model Routing Engine

> 작업 유형과 난이도에 따라 최적의 AI 모델을 추천하고, 비용/CO₂ 절감량을 계산하는 LangChain 기반 라우팅 엔진

---

## 실행 방법

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

서버 실행 후 접속:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/

---

## API 사용법

### POST /route

사용자 요청을 분석하여 최적 모델을 추천합니다.

**요청:**
```json
{
  "query": "이 이메일 문장을 자연스럽게 고쳐줘",
  "policy": "balanced",
  "baseline_model": "claude-sonnet"
}
```

**policy 옵션:** `cost_first`, `carbon_first`, `quality_first`, `balanced`

**응답:**
```json
{
  "query": "이 이메일 문장을 자연스럽게 고쳐줘",
  "task_type": "writing_edit",
  "difficulty": "low",
  "policy": "balanced",
  "baseline_model": "claude-sonnet",
  "selected_model": "gemini-flash",
  "reason": "'문장 수정' 작업(난이도: 낮은)에 대해 비용·탄소·품질 균형 정책을 적용했습니다. Gemini Flash은 저비용·저탄소 모델로, 이 작업에 충분한 성능을 제공하면서 기준 모델 대비 비용과 탄소를 절감합니다.",
  "estimated_tokens": {
    "input": 44,
    "output": 100,
    "total": 144
  },
  "cost": {
    "selected_usd": 0.000033,
    "baseline_usd": 0.001632,
    "saved_usd": 0.001599,
    "percent_cheaper": 98.0
  },
  "carbon": {
    "selected_g": 0.036,
    "baseline_g": 0.125568,
    "saved_g": 0.089568,
    "percent_less_co2": 71.3
  },
  "alternatives": ["gemma-4-27b-a4b", "gemma-4-e2b"],
  "mock_answer": "[Gemini Flash 응답] 빠르고 간결한 답변을 제공합니다..."
}
```

### POST /plan ⭐ (멀티스텝 라우팅)

복합 요청을 서브태스크로 분해하고, **각 스텝마다 최적 모델을 배정**하여 시뮬레이션합니다.

**요청:**
```json
{
  "query": "최신 AI 트렌드 자료를 찾아서 정리하고, Python으로 코드를 구현한 다음, 보고서로 만들어줘",
  "policy": "balanced",
  "baseline_model": "claude-sonnet"
}
```

**응답 (핵심 부분):**
```json
{
  "is_multi_step": true,
  "total_steps": 4,
  "steps": [
    { "step": 1, "action": "자료 검색 및 정보 수집", "selected_model": "gemini-flash", "task_type": "summarize" },
    { "step": 2, "action": "코드 작성", "selected_model": "gemma-4-27b-a4b", "task_type": "coding" },
    { "step": 3, "action": "정보 요약 및 정리", "selected_model": "gemini-flash", "task_type": "summarize" },
    { "step": 4, "action": "보고서/문서 작성", "selected_model": "gemini-flash", "task_type": "writing_edit" }
  ],
  "total_tokens": 1619,
  "total_cost_usd": 0.000237,
  "baseline_total_cost_usd": 0.018465,
  "saved_cost_usd": 0.018228,
  "percent_cheaper": 98.7,
  "saved_co2_g": 1.048808,
  "percent_less_co2": 74.3,
  "model_assignment": {
    "gemini-flash": ["자료 검색 및 정보 수집", "정보 요약 및 정리", "보고서/문서 작성"],
    "gemma-4-27b-a4b": ["코드 작성"]
  }
}
```

핵심: "전부 Claude Sonnet으로 처리하면 $0.018" vs "스텝별 최적 모델 배정하면 $0.0002" → **98.7% 절감**

### GET /models

모델 카탈로그 조회

### GET /policies

운영 정책 목록 조회

---

## Swagger 테스트

1. 서버 실행: `uvicorn main:app --reload`
2. 브라우저에서 http://localhost:8000/docs 접속
3. `POST /route` 엔드포인트 클릭 → "Try it out"
4. Request body에 JSON 입력 후 "Execute"

---

## curl 테스트

```bash
# 서버 상태 확인
curl http://localhost:8000/

# ─── 단일 라우팅 (POST /route) ───

# 단순 질문 (균형 정책)
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "블록체인이 뭐야?", "policy": "balanced"}'

# 문장 수정 (탄소 우선)
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{"query": "이 이메일 문장을 자연스럽게 고쳐줘", "policy": "carbon_first"}'

# ─── 멀티스텝 플랜 (POST /plan) ⭐ ───

# 복합 요청: 자료 검색 + 코딩 + 보고서
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "최신 AI 트렌드 자료를 찾아서 정리하고, Python으로 데이터 시각화 코드를 구현한 다음, 보고서로 만들어줘", "policy": "balanced"}'

# 복합 요청: 설계 + 구현 + 테스트 (품질 우선)
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "마이크로서비스 아키텍처를 설계하고, FastAPI로 API 서버를 구현하고, 테스트 코드도 작성해줘", "policy": "quality_first"}'

# 모델 카탈로그 조회
curl http://localhost:8000/models

# 정책 목록 조회
curl http://localhost:8000/policies
```

Windows PowerShell에서 테스트:
```powershell
# 서버 상태 확인
Invoke-RestMethod http://localhost:8000/

# POST /route
$body = @{query="블록체인이 뭐야?"; policy="balanced"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/route -Body $body -ContentType "application/json"
```

---

## 테스트 스크립트

```bash
# ─── 단일 라우팅 테스트 ───
python scripts/test_route.py          # 서버 실행 상태에서
python scripts/test_route.py --offline  # 서버 없이

# ─── 멀티스텝 플랜 시뮬레이션 ⭐ ───
python scripts/test_plan.py           # 서버 실행 상태에서
python scripts/test_plan.py --offline   # 서버 없이
```

`test_plan.py`는 복합 요청 5개를 자동으로 분해하고, 각 스텝별 모델 배정과 총 절감량을 출력합니다.

---

## 프로젝트 구조

```
backend/
├─ main.py                     # FastAPI 서버 진입점
├─ router/                     # 라우팅 엔진 (핵심 로직)
│  ├─ task_classifier.py       # 작업 유형/난이도 분류
│  ├─ task_decomposer.py       # 복합 요청 → 서브태스크 분해 ⭐
│  ├─ plan_executor.py         # 멀티스텝 실행 + 합산 ⭐
│  ├─ model_catalog.py         # 모델 메타데이터 관리
│  ├─ routing_policy.py        # 정책별 가중치 정의
│  ├─ model_selector.py        # 최종 모델 선택 로직
│  └─ carbon_estimator.py      # 비용/CO₂ 절감량 계산
├─ llm/                        # LLM 호출 레이어 (라우터와 분리)
│  ├─ base_client.py           # 추상 인터페이스
│  ├─ mock_client.py           # Mock 클라이언트 (현재 사용)
│  └─ bedrock_client.py        # Bedrock 스켈레톤 (향후)
├─ prompts/
│  └─ router_system_prompt.txt # LLM 분류기용 시스템 프롬프트
├─ schemas/
│  └─ route_response.py        # Pydantic 요청/응답 스키마
├─ scripts/
│  ├─ test_route.py            # 단일 라우팅 테스트
│  └─ test_plan.py             # 멀티스텝 시뮬레이션 테스트 ⭐
├─ examples/
│  └─ route_examples.json      # 샘플 입력 데이터
├─ requirements.txt
└─ README.md
```

---

## 핵심 설계 원칙

### 1. 라우팅 엔진 ↔ LLM 호출부 분리

```
[router/] → 어떤 모델을 쓸지 결정
[llm/]    → 실제 모델 호출 (또는 mock)
```

이 두 레이어는 완전히 독립적입니다. 라우팅 엔진은 LLM API를 모릅니다.

### 2. Bedrock 연결 방법

AWS Bedrock 권한이 활성화되면:

1. `llm/bedrock_client.py`의 TODO를 구현
2. `main.py`에서 클라이언트 교체:

```python
# 변경 전
from llm.mock_client import MockLLMClient
llm_client = MockLLMClient()

# 변경 후
from llm.bedrock_client import BedrockLLMClient
llm_client = BedrockLLMClient(region="us-east-1")
```

라우팅 로직(`router/`)은 수정 불필요.

### 3. LangChain 확장

현재 `task_classifier`와 `model_selector`는 rule-based이지만,
LangChain Runnable 인터페이스로 래핑되어 있어 LLM 기반으로 교체 가능합니다:

```python
from router.task_classifier import task_classifier_runnable
from router.model_selector import model_selector_runnable

# 체인 조합
chain = task_classifier_runnable | model_selector_runnable
result = chain.invoke({"query": "...", "policy": "balanced"})
```

향후 LLM 기반 분류기로 바꿀 때:
```python
from langchain_core.runnables import RunnableSequence
from langchain_aws import ChatBedrockConverse

llm = ChatBedrockConverse(model="anthropic.claude-3-haiku-...")
classifier_chain = prompt_template | llm | json_output_parser
```

---

## 프론트엔드 연동

프론트엔드는 `POST /route`만 호출하면 됩니다.

- CORS는 이미 전체 허용 (`allow_origins=["*"]`)
- 응답 JSON 형식은 `schemas/route_response.py` 참고
- Swagger UI에서 정확한 스키마 확인 가능

---

## 모델 목록

| model_id | Provider | CO₂/token | Quality | 적합 작업 |
|----------|----------|-----------|---------|-----------|
| gemini-flash | Google | 0.250mg | 0.55 | 단순질의, 요약, 번역, 수정 |
| gpt-4o-mini | OpenAI | 0.350mg | 0.65 | 단순질의, 번역, 코딩 |
| claude-haiku | Anthropic | 0.300mg | 0.60 | 요약, 수정, 단순질의 |
| gpt-4o | OpenAI | 0.699mg | 0.85 | 코딩, 추론, 기획, 민감 |
| gemini-pro | Google | 0.450mg | 0.78 | 코딩, 추론, 기획 |
| claude-sonnet | Anthropic | 0.872mg | 0.92 | 추론, 코딩, 기획, 민감 |
| claude-opus | Anthropic | 0.950mg | 0.97 | 추론, 민감, 기획 |
| gemma-4-e2b | Google Open | 0.120mg | 0.40 | 단순질의, 번역 |
| gemma-4-27b-a4b | Google Open | 0.180mg | 0.58 | 단순질의, 코딩 |
