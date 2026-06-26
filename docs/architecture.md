# ECOROUTE 아키텍처

## 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                    │
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Sidebar  │  │  Main Panel  │  │  Dashboard         │    │
│  │  - 정책    │  │  - 입력      │  │  - 통계            │    │
│  │  - 통계    │  │  - 결과 카드  │  │  - 모델 사용비율    │    │
│  │  - 모델    │  │  - 히스토리   │  │  - CO₂ 환산       │    │
│  └──────────┘  └──────────────┘  └────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                   Backend (FastAPI)                           │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ task_classifier  │  │ model_catalog   │                  │
│  │ (작업 분류)       │  │ (모델 관리)      │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                     │                            │
│  ┌────────▼─────────────────────▼────────┐                  │
│  │         model_selector                 │                  │
│  │         (최종 모델 선택)                 │                  │
│  └────────┬──────────────────────────────┘                  │
│           │                                                  │
│  ┌────────▼────────┐  ┌─────────────────┐                  │
│  │routing_policy   │  │carbon_estimator │                  │
│  │(정책 가중치)     │  │(비용/CO₂ 계산)  │                  │
│  └─────────────────┘  └─────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
```

## 모듈별 역할

| 모듈 | 파일 | 역할 | LangChain 확장 |
|------|------|------|---------------|
| 작업 분류기 | `task_classifier.py` | 입력을 카테고리+난이도로 분류 | LLM Chain으로 대체 |
| 모델 카탈로그 | `model_catalog.py` | 모델 메타데이터 관리 | DB/Config로 이전 |
| 라우팅 정책 | `routing_policy.py` | 가중치 정의 | 사용자별 동적 정책 |
| 모델 선택기 | `model_selector.py` | 종합 점수 → 모델 선택 | Agent로 대체 |
| 탄소 계산기 | `carbon_estimator.py` | 비용/CO₂ 절감량 계산 | 실시간 API 연동 |

## LangChain 확장 포인트

### Phase 1: Classifier를 LLM으로 대체
```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

classifier_prompt = PromptTemplate(
    input_variables=["query"],
    template="다음 요청을 분류하세요: {query}\n작업유형: ...\n난이도: ..."
)
# 경량 모델(Gemini Flash)로 분류 수행
```

### Phase 2: Router를 Agent로 대체
```python
from langchain.agents import AgentExecutor
# 모델 선택을 Agent가 도구를 사용해 수행
```

### Phase 3: 실제 모델 호출
```python
from langchain.chat_models import ChatOpenAI, ChatAnthropic
# 선택된 모델로 실제 응답 생성
```
