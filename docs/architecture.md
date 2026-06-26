# ECOCACHE 아키텍처

## 시스템 구조

```
┌──────────────────────────────────────────────────────────────┐
│                      Client (프론트엔드)                        │
│              POST /plan/graph 호출 → 그래프 렌더링               │
└──────────────────────────────┬───────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼───────────────────────────────┐
│                      Backend (FastAPI)                         │
│                          main.py                               │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ router/llm_classifier.py                                 │  │
│  │  Claude Haiku 4.5가 요청 분해 + 분류 + 모델 추천          │  │
│  └───────────────────────────┬────────────────────────────┘  │
│                              │                                 │
│  ┌──────────────────┐  ┌─────▼──────────┐  ┌──────────────┐  │
│  │ model_catalog.py  │  │ routing_policy │  │carbon_       │  │
│  │ (모델 스펙)        │  │ (정책 가중치)   │  │estimator.py  │  │
│  └──────────────────┘  └────────────────┘  └──────────────┘  │
│                              │                                 │
│  ┌───────────────────────────▼────────────────────────────┐  │
│  │ llm/anthropic_client.py                                  │  │
│  │  각 스텝을 Claude Haiku 4.5로 실제 실행                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Anthropic Claude API │
                    └──────────────────────┘
```

## 모듈별 역할

| 모듈 | 파일 | 역할 |
|------|------|------|
| 분류/분해/추천 | `router/llm_classifier.py` | Claude Haiku가 요청을 서브태스크로 분해하고 각 스텝에 모델 추천 |
| 모델 카탈로그 | `router/model_catalog.py` | 모델 9개의 비용/CO₂/품질 점수 관리 |
| 라우팅 정책 | `router/routing_policy.py` | cost/carbon/quality/balanced 가중치 + 메타데이터 |
| 탄소 계산기 | `router/carbon_estimator.py` | 실측 토큰 기반 비용/CO₂ 계산 |
| LLM 클라이언트 | `llm/anthropic_client.py` | Claude Haiku 4.5 실제 호출 |
| 응답 스키마 | `schemas/graph_response.py` | 노드-엣지 그래프 형태 정의 |

## 실행 흐름

```
POST /plan/graph
   │
   ▼ ① 분해 + 추천
   router/llm_classifier.py → Claude Haiku가 JSON으로 서브태스크 목록 반환
   │
   ▼ ② 각 스텝 실제 수행
   llm/anthropic_client.py → 실제 AI 응답 생성 (실측 토큰)
   router/carbon_estimator.py → 비용/CO₂ 계산 (선택 모델 vs baseline)
   │
   ▼ ③ 합산 + 변환
   노드-엣지 그래프 + summary로 응답
```

## 설계 원칙: 라우팅 엔진 ↔ LLM 호출부 분리

```
[router/]  → 어떤 모델을 쓸지 결정 (LLM 호출 API를 모름)
[llm/]     → 실제 모델 호출 (base_client.py 인터페이스 구현)
```

`llm/base_client.py`의 추상 인터페이스 덕분에, 향후 OpenAI/Google 등 실제
멀티 프로바이더를 붙일 때 `llm/`에 클라이언트만 추가하면 됩니다.
라우팅 로직(`router/`)은 수정할 필요가 없습니다.

## 향후 확장

### 실제 멀티 프로바이더 연결
현재는 모든 응답을 Claude Haiku 4.5가 생성합니다.
각 추천 모델의 실제 API를 연결하려면:

```python
# llm/openai_client.py, llm/google_client.py 추가 (base_client 구현)
# main.py에서 recommended_model에 따라 적절한 클라이언트 선택
```

### 점수 기반 결정적 라우팅 (옵션)
현재는 Claude Haiku의 판단(LLM 기반)으로 모델을 추천합니다.
일관성이 중요하면 `model_catalog`의 점수를 가중합하는 결정적 알고리즘으로
보완할 수 있습니다:

```
final_score = quality×w1 + cost×w2 + carbon×w3 + speed×w4 + task_fit
```
