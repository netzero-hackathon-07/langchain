# 🌿 ECOROUTE - AI Model Carbon-Aware Router

> 탄소중립에 기여하기 위한 저전력/고효율 LLM 기반 서비스

모든 요청을 하나의 고성능 LLM에 보내는 대신, **작업 유형과 난이도에 따라 가장 적합한 AI 모델을 자동 추천/라우팅**하여 비용과 CO₂ 배출량을 줄이는 서비스입니다.

---

## 핵심 기능

- **작업 유형 자동 분류**: 단순 질의, 요약, 번역, 문장 수정, 코딩, 추론, 기획, 민감 답변
- **난이도 판단**: low / medium / high
- **운영 정책**: 비용 우선 / 탄소 우선 / 품질 우선 / 균형
- **모델 추천**: 6개 모델 중 최적 선택 + 이유 + 대체 모델
- **절감량 계산**: baseline(Claude Sonnet) 대비 비용/CO₂/토큰 절감률

## 프로젝트 구조

```
ecoroute/
├─ frontend/          # React + Vite (SPA)
│  └─ src/
│     ├─ components/  # Header, Sidebar, MainPanel, ResultCard, Dashboard
│     ├─ api.js       # API 클라이언트 (mock 포함)
│     └─ App.jsx
├─ backend/           # Python FastAPI
│  ├─ main.py         # 서버 진입점
│  ├─ router/
│  │  ├─ task_classifier.py   # 작업 분류
│  │  ├─ model_catalog.py     # 모델 메타데이터
│  │  ├─ routing_policy.py    # 정책 가중치
│  │  ├─ model_selector.py    # 모델 선택 로직
│  │  └─ carbon_estimator.py  # 비용/CO₂ 계산
│  └─ schemas/
│     └─ route_response.py    # 응답 스키마
├─ docs/
│  ├─ carbon_calculation.md   # CO₂ 계산 기준
│  └─ architecture.md         # 아키텍처 문서
└─ README.md
```

## 실행 방법

### 프론트엔드 (React)

```bash
cd frontend
npm install
npm run dev
```

- http://localhost:5173 에서 접속
- 기본 mock 모드로 동작하므로 **백엔드 없이도 실행 가능**

### 백엔드 (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

- http://localhost:8000 에서 API 서버 실행
- http://localhost:8000/docs 에서 Swagger UI 확인

### 프론트 + 백 연동

1. `frontend/src/api.js`에서 `USE_MOCK = false`로 변경
2. 백엔드 실행 (port 8000)
3. 프론트엔드 실행 (port 5173, Vite proxy 설정 완료)

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/route` | 모델 라우팅 (핵심) |
| GET | `/api/models` | 모델 카탈로그 조회 |
| GET | `/api/policies` | 정책 목록 조회 |
| GET | `/api/stats` | 대시보드 통계 |
| POST | `/api/stats/reset` | 통계 초기화 |

## 모델 후보

| 모델 | CO₂/token | 특징 |
|------|-----------|------|
| Gemini Flash | 0.250 mg | 저비용, 저탄소, 빠른 응답 |
| GPT-4o mini | 0.350 mg | 범용 저비용 모델 |
| Claude Haiku | 0.300 mg | 빠른 요약/문장 처리 |
| GPT-4o | 0.699 mg | 균형형 고품질 모델 |
| Gemini Pro | 0.450 mg | 중상급 범용 모델 |
| Claude Sonnet | 0.872 mg | 복잡한 추론/코딩 (baseline) |

## 향후 확장 포인트

### LangChain 연동
- `task_classifier.py` → LLM Chain (경량 모델로 분류)
- `model_selector.py` → LangChain Agent
- 실제 모델 호출 후 응답 반환

### 실제 API 연동
- OpenAI, Anthropic, Google API 키 설정
- 라우팅 후 선택된 모델로 실제 응답 생성
- 응답 품질 피드백 루프

### 추가 기능
- 사용자별 예산/탄소 한도 설정
- 월간 리포트 자동 생성
- 실시간 탄소 강도(Carbon Intensity) API 연동
- 모델 응답 품질 A/B 테스트

---

## 기술 스택

- **Frontend**: React 18, Vite 5, CSS Variables
- **Backend**: Python 3.10+, FastAPI, Pydantic
- **향후**: LangChain, tiktoken, PostgreSQL

## 라이선스

MIT License
