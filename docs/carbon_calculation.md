# CO₂ 계산 기준

## 모델별 탄소 배출량

| 모델 계열 | CO₂ per token | 비고 |
|-----------|---------------|------|
| Gemini (Flash/Pro) | 0.250 mgCO₂/token | Google 재생에너지 데이터센터 기반 |
| GPT-5 기준 (GPT-4o/mini) | 0.699 mgCO₂/token | OpenAI 추정치 |
| Claude-3.7 Sonnet 기준 | 0.872 mgCO₂/token | Anthropic 추정치 |

## 계산 방법

1. **토큰 측정**: Claude API 응답의 실측 토큰(input/output) 사용
2. **CO₂ 산출**: `총 토큰 × 모델별 mgCO₂/token ÷ 1000 = CO₂(g)`
3. **절감량**: `Baseline(Claude Sonnet) CO₂ - 선택 모델 CO₂ = 절감량`

## 환산 기준

- 자동차 1km 주행 = 약 120g CO₂
- 소나무 1그루 연간 흡수량 = 약 5,000g CO₂
- 스마트폰 1회 충전 = 약 8.22g CO₂

## 참고

- 이 수치는 추정치이며, 실제 데이터센터 위치, 시간대, 부하에 따라 달라질 수 있습니다.
- 향후 실시간 탄소 강도(Carbon Intensity) API 연동으로 정확도를 개선할 수 있습니다.
- 참고 소스: IEA, Google Environmental Report, ML CO2 Impact 논문
