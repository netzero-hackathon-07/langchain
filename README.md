# 🌿 ECOCACHE - AI Model Carbon-Aware Router

> 탄소중립에 기여하기 위한 저전력/고효율 LLM 기반 라우팅 서비스

복합 요청을 **여러 서브태스크로 분해**하고, 각 스텝에 가장 적합한 AI 모델을 배정하여 비용과 CO₂ 배출량을 줄이는 백엔드 엔진입니다. Claude Haiku 4.5가 분해/분류/모델추천을 직접 수행합니다.

---

## 핵심 아이디어

모든 요청을 하나의 고성능 모델(예: Claude Sonnet)에 보내는 대신:

```
"자료 찾아서 코딩하고 보고서 써줘"
   → Step 1: 자료 검색   → gemini-flash  (단순 → 저비용)
   → Step 2: 코드 작성   → gpt-4o        (복잡 → 고성능)
   → Step 3: 보고서 작성 → claude-haiku  (중간)

결과: 전부 Sonnet으로 처리한 것 대비 비용 51%, CO₂ 35% 절감
```

토큰을 아끼는 만큼 전력·비용·탄소 배출이 줄어듭니다.

---

## 프로젝트 구조

```
ecocache/
├─ backend/          # FastAPI 라우팅 엔진 (메인 작업물)
│  ├─ main.py
│  ├─ llm/           # LLM 호출 (Claude Haiku 4.5)
│  ├─ router/        # 분해/분류/모델추천/탄소계산
│  ├─ schemas/       # 응답 스키마 (노드-엣지 그래프)
│  └─ scripts/       # 데모 스크립트
├─ docs/             # 아키텍처 / CO₂ 계산 기준 문서
└─ README.md
```

> 자세한 실행/API 사용법은 [`backend/README.md`](backend/README.md) 참고

---

## 빠른 시작

```bash
cd backend
pip install -r requirements.txt
# .env에 ANTHROPIC_API_KEY 설정
uvicorn main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- 메인 엔드포인트: `POST /plan/graph`

---

## 주요 API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/plan/graph` | 복합 요청 → 노드-엣지 그래프 (프론트 시각화용) |
| POST | `/plan` | 복합 요청 → flat 리스트 결과 |
| GET | `/usage` | API 사용량 / 예산 잔액 |
| GET | `/models` | 모델 카탈로그 |
| GET | `/policies` | 운영 정책 |

**운영 정책:** `cost_first` / `carbon_first` / `quality_first` / `balanced`

---

## 모델 카탈로그 (추천 대상)

| 모델 | CO₂/token | 특징 |
|------|-----------|------|
| gemini-flash | 0.250 mg | 저비용·저탄소, 단순 작업 |
| gpt-4o-mini | 0.350 mg | 범용 저비용 |
| claude-haiku | 0.300 mg | 빠른 요약/문장 |
| gemini-pro | 0.450 mg | 중상급 범용 |
| gpt-4o | 0.699 mg | 균형형 고품질 |
| claude-sonnet | 0.872 mg | 복잡한 추론 (기본 baseline) |

> 실제 응답 생성은 현재 전부 Claude Haiku 4.5로 수행됩니다.
> 향후 각 모델의 실제 API를 `llm/`에 추가하면 멀티 프로바이더로 확장됩니다.

---

## 기술 스택

- Python 3.11, FastAPI, Pydantic v2
- Anthropic Claude API (Haiku 4.5)
- LangChain Core (확장 대비)
