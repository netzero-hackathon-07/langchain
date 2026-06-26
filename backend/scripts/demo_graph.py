"""ECOCACHE - 그래프 형태 응답 데모"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

query = sys.argv[1] if len(sys.argv) > 1 else (
    "AWS 클라우드 아키텍처 자료를 조사해서 정리하고, "
    "Python FastAPI로 API 서버를 코딩하고, "
    "최종 보고서로 작성해줘"
)
policy = sys.argv[2] if len(sys.argv) > 2 else "balanced"

try:
    r = httpx.post(f"{BASE_URL}/plan/graph", json={"query": query, "policy": policy})
except httpx.ConnectError:
    print("서버가 꺼져있습니다: uvicorn main:app --reload")
    sys.exit(1)

data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))
