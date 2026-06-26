# ECOCACHE Backend - AI Model Routing Engine

> Claude Haiku 4.5가 복합 요청을 서브태스크로 분해하고, 각 스텝에 최적 AI 모델을 추천/실행하여 비용·CO₂를 절감하는 라우팅 엔진

---

## 핵심 개념

```
"자료 찾아서 코딩하고 보고서 써줘"  (복합 요청)
        │
        ▼  Claude Haiku 4.5가 분석
   ┌─────────────────────────────────────┐
   │ Step 1: 자료 검색  → gemini-flash    │  (단순 → 저비용 모델)
   │ Step 2: 코드 작성  → gpt-4o          │  (복잡 → 고성능 모델)
   │ Step 3: 보고서 작성 → claude-haiku   │  (중간 → 중간 모델)
   └─────────────────────────────────────┘
        │
        ▼  각 스텝 실제 수행 + 합산
   "전부 claude-sonnet으로 했으면 $0.022 → 나눠서 $0.011 (51% 절감)"
```

단일 고성능 모델로 모든 요청을 처리하는 대신, **작업을 쪼개서 각 스텝에 적합한 모델을 배정**하여 비용과 탄소 배출을 줄입니다.

---

## 실행 방법

```bash
cd backend
pip install -r requirements.txt
```

`.env` 파일에 API 키 설정 (`.env.example`을 복사해서 만들면 편함):
```bash
copy .env.example .env     # Windows
# cp .env.example .env      # Mac/Linux
```
`.env` 내용:
```
ANTHROPIC_API_KEY=sk-ant-...
```

서버 실행:
```bash
uvicorn main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- 사용량 확인: http://localhost:8000/usage

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/plan/graph` | **메인.** 복합 요청 → 노드-엣지 그래프 (프론트 시각화용) |
| POST | `/plan` | 복합 요청 → flat 리스트 결과 |
| GET | `/usage` | API 사용량 / 예산($5) 잔액 |
| GET | `/models` | 모델 카탈로그 조회 |
| GET | `/policies` | 운영 정책 목록 |
| GET | `/` | 헬스 체크 |

### POST /plan/graph 요청

```json
{
  "query": "최신 AI 트렌드를 조사하고, 핵심을 요약한 다음, 블로그 글로 작성해줘",
  "policy": "balanced",
  "baseline_model": "claude-sonnet"
}
```

**policy 옵션:** `cost_first` / `carbon_first` / `quality_first` / `balanced`

### 응답 (노드-엣지 그래프)

```json
{
  "id": "...",
  "name": "조사 → 요약 → 블로그 작성",
  "nodes": [
    {
      "id": "node-001",
      "role": "analyst",
      "model": "gpt-4o",
      "label": "최신 AI 트렌드 조사",
      "task_type": "reasoning",
      "difficulty": "medium",
      "estimated_input_tokens": 168,
      "estimated_output_tokens": 458,
      "cost_usd": 0.005,
      "co2_g": 0.437574,
      "baseline_cost_usd": 0.007374,
      "baseline_co2_g": 0.545872,
      "reason": "최신 정보를 종합 분석하는 추론 작업으로 gpt-4o가 적합",
      "position": { "x": 100, "y": 200 },
      "answer": "# 최신 AI 트렌드 2024 ... (실제 AI 응답)"
    }
  ],
  "edges": [
    {
      "id": "edge-001",
      "source_node_id": "node-001",
      "target_node_id": "node-002",
      "data_transfer": "context_pass",
      "token_overhead": 200
    }
  ],
  "summary": {
    "total_tokens": 1866,
    "total_cost_usd": 0.01076,
    "baseline_total_cost_usd": 0.02199,
    "saved_cost_usd": 0.01123,
    "percent_cheaper": 51.1,
    "saved_co2_g": 0.569768,
    "percent_less_co2": 35.0,
    "model_assignment": { "gpt-4o": [...], "gemini-flash": [...] }
  }
}
```

---

## curl 테스트

```bash
curl -X POST http://localhost:8000/plan/graph ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"자료를 조사하고 코딩한 다음 보고서로 정리해줘\", \"policy\": \"balanced\"}"
```

PowerShell:
```powershell
$body = @{query="자료를 조사하고 코딩한 다음 보고서로 정리해줘"; policy="balanced"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/plan/graph -Body $body -ContentType "application/json"
```

## 테스트 스크립트

```bash
# 서버 실행 상태에서
python scripts/demo_live.py "원하는 요청"       # 사람이 읽기 쉬운 형태로 출력
python scripts/demo_graph.py "원하는 요청"      # 그래프 JSON 전체 출력
```

---

## 프로젝트 구조

```
backend/
├─ main.py                      # FastAPI 서버 + 실행 흐름
├─ .env                         # API 키 (git 제외)
├─ requirements.txt
│
├─ llm/                         # LLM 호출 레이어 (라우팅과 분리)
│  ├─ base_client.py            # 추상 인터페이스
│  └─ anthropic_client.py       # Claude Haiku 4.5 실제 호출
│
├─ router/                      # 라우팅 엔진
│  ├─ llm_classifier.py         # Haiku가 분해 + 분류 + 모델 추천 (핵심)
│  ├─ model_catalog.py          # 모델 9개 스펙 (비용/CO₂/품질)
│  ├─ carbon_estimator.py       # 비용/CO₂ 계산
│  └─ routing_policy.py         # 정책별 가중치 + 메타데이터
│
├─ schemas/                     # Pydantic 응답 스키마
│  ├─ route_response.py         # PlanRequest, PlanResponse, StepDetail
│  └─ graph_response.py         # PipelineGraphResponse (노드-엣지)
│
└─ scripts/                     # 테스트/데모
   ├─ demo_live.py
   └─ demo_graph.py
```

---

## 동작 흐름

```
POST /plan/graph
   │
   ▼ main.py: plan_and_execute()
   │
   ├─① router/llm_classifier.py
   │     Claude Haiku가 요청 분해 + 각 스텝 모델 추천
   │
   ├─② 각 스텝 반복: llm/anthropic_client.py로 실제 AI 응답 생성
   │     → router/carbon_estimator.py로 비용/CO₂ 계산 (실측 토큰 기반)
   │
   └─③ 합산 + 노드-엣지 그래프로 변환 → 응답
```

---

## 비용 / 예산

- 모든 호출은 **Claude Haiku 4.5** 사용 (가장 저렴한 모델)
- `$5` 예산 한도, 초과 시 429 에러
- `GET /usage`로 실시간 사용량 확인
- 요청 1건당 약 $0.005 (~1000회 호출 가능)

> 참고: `model_catalog.py`의 gemini-flash/gpt-4o 등은 **추천 대상 카탈로그**이며,
> 실제 응답 생성은 전부 Claude Haiku 4.5가 각 모델 역할을 시뮬레이션합니다.
> 향후 각 모델의 실제 API를 연결하면 `llm/`에 클라이언트만 추가하면 됩니다.

---

## 향후 확장 (실제 멀티 프로바이더 연결)

`llm/base_client.py` 인터페이스를 구현하는 클라이언트를 추가하고,
`main.py`에서 모델별로 분기하면 각 모델의 실제 API를 호출할 수 있습니다.

```python
# llm/openai_client.py, llm/google_client.py 등 추가
# main.py에서 recommended_model에 따라 클라이언트 선택
```
