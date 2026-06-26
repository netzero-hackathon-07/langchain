/**
 * ECOROUTE API 클라이언트
 * 
 * 개발 시 백엔드 미실행 상태에서도 동작하도록 mock 데이터 포함.
 * VITE_USE_MOCK=true 환경변수로 mock 모드 전환 가능.
 */

const API_BASE = '/api';
const USE_MOCK = true; // 백엔드 미실행 시 true로 설정

// ─── Mock 데이터 ───────────────────────────────────

const MOCK_MODELS = {
  "Gemini Flash": {
    provider: "google",
    cost_per_1k_input: 0.000075,
    cost_per_1k_output: 0.0003,
    co2_per_token_mg: 0.250,
    quality_score: 0.55,
    speed_score: 0.95,
    strengths: ["단순 질의", "요약", "번역", "문장 수정"],
  },
  "GPT-4o mini": {
    provider: "openai",
    cost_per_1k_input: 0.00015,
    cost_per_1k_output: 0.0006,
    co2_per_token_mg: 0.350,
    quality_score: 0.65,
    speed_score: 0.85,
    strengths: ["단순 질의", "요약", "번역", "문장 수정", "코딩 보조"],
  },
  "Claude Haiku": {
    provider: "anthropic",
    cost_per_1k_input: 0.00025,
    cost_per_1k_output: 0.00125,
    co2_per_token_mg: 0.300,
    quality_score: 0.60,
    speed_score: 0.90,
    strengths: ["요약", "문장 수정", "단순 질의", "번역"],
  },
  "GPT-4o": {
    provider: "openai",
    cost_per_1k_input: 0.0025,
    cost_per_1k_output: 0.01,
    co2_per_token_mg: 0.699,
    quality_score: 0.85,
    speed_score: 0.70,
    strengths: ["코딩 보조", "복잡한 추론", "기획/창작", "중요/민감 답변"],
  },
  "Gemini Pro": {
    provider: "google",
    cost_per_1k_input: 0.00125,
    cost_per_1k_output: 0.005,
    co2_per_token_mg: 0.450,
    quality_score: 0.78,
    speed_score: 0.75,
    strengths: ["코딩 보조", "복잡한 추론", "기획/창작", "요약"],
  },
  "Claude Sonnet": {
    provider: "anthropic",
    cost_per_1k_input: 0.003,
    cost_per_1k_output: 0.015,
    co2_per_token_mg: 0.872,
    quality_score: 0.92,
    speed_score: 0.60,
    strengths: ["복잡한 추론", "코딩 보조", "기획/창작", "중요/민감 답변"],
  },
};

const TASK_KEYWORDS = {
  "단순 질의": ["뭐야", "알려줘", "무엇", "언제", "어디", "누구", "왜", "어떻게", "what", "how", "tell"],
  "요약": ["요약", "줄여", "정리", "핵심", "summary", "간단히"],
  "번역": ["번역", "translate", "영어로", "한국어로"],
  "문장 수정": ["고쳐", "수정", "다듬", "교정", "자연스럽게", "rewrite", "polish"],
  "코딩 보조": ["코드", "코딩", "함수", "구현", "리팩토링", "버그", "code", "refactor"],
  "복잡한 추론": ["분석", "비교", "평가", "설계", "아키텍처", "최적화", "전략"],
  "기획/창작": ["기획", "작성", "창작", "아이디어", "브레인스토밍", "시나리오"],
  "중요/민감 답변": ["법률", "의료", "금융", "계약", "보안", "개인정보"],
};

function mockClassify(query) {
  const lower = query.toLowerCase();
  let bestType = "단순 질의";
  let bestScore = 0;

  for (const [type, keywords] of Object.entries(TASK_KEYWORDS)) {
    const score = keywords.filter(kw => lower.includes(kw)).length;
    if (score > bestScore) {
      bestScore = score;
      bestType = type;
    }
  }

  // 난이도
  let difficulty = "low";
  if (lower.length > 200 || ["복잡한 추론", "중요/민감 답변"].some(t => t === bestType)) {
    difficulty = "high";
  } else if (lower.length > 80 || ["코딩 보조", "기획/창작"].some(t => t === bestType)) {
    difficulty = "medium";
  }

  return { task_type: bestType, difficulty };
}

function mockSelectModel(taskType, difficulty, policy) {
  const models = Object.entries(MOCK_MODELS);
  
  const weights = {
    cost_first: { cost: 0.6, co2: 0.25, quality: 0.15 },
    carbon_first: { cost: 0.15, co2: 0.6, quality: 0.25 },
    quality_first: { cost: 0.15, co2: 0.1, quality: 0.75 },
    balanced: { cost: 0.33, co2: 0.34, quality: 0.33 },
  }[policy] || { cost: 0.33, co2: 0.34, quality: 0.33 };

  const scored = models.map(([name, info]) => {
    const maxCost = 0.015;
    const avgCost = (info.cost_per_1k_input + info.cost_per_1k_output) / 2;
    const costScore = 1 - Math.min(avgCost / maxCost, 1);
    const co2Score = 1 - Math.min(info.co2_per_token_mg / 0.872, 1);
    const qualityScore = info.quality_score;
    const taskBonus = info.strengths.includes(taskType) ? 0.15 : 0;
    const diffMod = difficulty === "high" && qualityScore >= 0.8 ? 0.1 :
                    difficulty === "high" ? -0.1 :
                    difficulty === "medium" && qualityScore >= 0.65 ? 0.05 : 0;

    const total = weights.cost * costScore + weights.co2 * co2Score + 
                  weights.quality * (qualityScore + diffMod) + taskBonus;
    return { name, score: total };
  });

  scored.sort((a, b) => b.score - a.score);
  return {
    selected: scored[0].name,
    alternatives: [scored[1].name, scored[2].name],
  };
}

function mockRoute(query, policy) {
  const { task_type, difficulty } = mockClassify(query);
  const { selected, alternatives } = mockSelectModel(task_type, difficulty, policy);

  const inputTokens = Math.max(query.length * 2, 20);
  const outputMap = {
    "단순 질의": { low: 100, medium: 200, high: 400 },
    "요약": { low: 150, medium: 300, high: 500 },
    "번역": { low: 120, medium: 250, high: 500 },
    "문장 수정": { low: 100, medium: 200, high: 350 },
    "코딩 보조": { low: 200, medium: 500, high: 1000 },
    "복잡한 추론": { low: 300, medium: 600, high: 1200 },
    "기획/창작": { low: 250, medium: 500, high: 1000 },
    "중요/민감 답변": { low: 200, medium: 400, high: 800 },
  };
  const outputTokens = outputMap[task_type]?.[difficulty] || 250;
  const totalTokens = inputTokens + outputTokens;

  // 비용 계산
  const selModel = MOCK_MODELS[selected];
  const baseModel = MOCK_MODELS["Claude Sonnet"];
  
  const selCost = (inputTokens / 1000) * selModel.cost_per_1k_input + (outputTokens / 1000) * selModel.cost_per_1k_output;
  const baseCost = (inputTokens / 1000) * baseModel.cost_per_1k_input + (outputTokens / 1000) * baseModel.cost_per_1k_output;
  const costSaved = Math.max(baseCost - selCost, 0);

  const selCo2 = (totalTokens * selModel.co2_per_token_mg) / 1000;
  const baseCo2 = (totalTokens * baseModel.co2_per_token_mg) / 1000;
  const co2Saved = Math.max(baseCo2 - selCo2, 0);

  const percentCheaper = baseCost > 0 ? ((costSaved / baseCost) * 100) : 0;
  const percentLessCo2 = baseCo2 > 0 ? ((co2Saved / baseCo2) * 100) : 0;
  const tokenSaved = baseCost > 0 ? Math.round((costSaved / baseCost) * totalTokens) : 0;

  const policyLabels = { cost_first: "비용 절감", carbon_first: "탄소 배출 최소화", quality_first: "응답 품질", balanced: "비용·탄소·품질 균형" };
  const diffLabels = { low: "낮은", medium: "중간", high: "높은" };

  let reason;
  if (selected === "Claude Sonnet") {
    reason = `'${task_type}' 작업이며 난이도가 ${diffLabels[difficulty]} 수준이라 고성능 모델이 필요합니다.`;
  } else {
    const co2Level = selModel.co2_per_token_mg < 0.4 ? "저탄소" : "중간 탄소";
    const costLevel = selModel.cost_per_1k_output < 0.002 ? "저비용" : "중간 비용";
    reason = `'${task_type}' 작업(난이도: ${diffLabels[difficulty]})에 대해 ${policyLabels[policy] || "균형"} 정책을 적용했습니다. ${selected}은 ${costLevel}·${co2Level} 모델로, 기준 모델 대비 비용과 탄소를 절감합니다.`;
  }

  return {
    query,
    task_type,
    difficulty,
    policy,
    baseline_model: "Claude Sonnet",
    selected_model: selected,
    reason,
    estimated_tokens: { input: inputTokens, output: outputTokens, total: totalTokens },
    savings: {
      cost_usd: parseFloat(costSaved.toFixed(6)),
      co2_g: parseFloat(co2Saved.toFixed(6)),
      token_saved: tokenSaved,
      percent_cheaper: parseFloat(percentCheaper.toFixed(1)),
      percent_less_co2: parseFloat(percentLessCo2.toFixed(1)),
    },
    alternatives,
  };
}

// ─── Cumulative stats (mock) ───────────────────────────────────

let mockStats = {
  total_requests_today: 0,
  total_cost_saved_usd: 0,
  total_co2_saved_g: 0,
  model_usage: {},
  average_model: "N/A",
  co2_equivalents: { car_km: 0, pine_trees_days: 0, phone_charges: 0 },
};

// ─── Public API ───────────────────────────────────

export async function routeQuery(query, policy = 'balanced') {
  if (USE_MOCK) {
    await new Promise(r => setTimeout(r, 400 + Math.random() * 600)); // fake latency
    const result = mockRoute(query, policy);
    // update mock stats
    mockStats.total_requests_today++;
    mockStats.total_cost_saved_usd += result.savings.cost_usd;
    mockStats.total_co2_saved_g += result.savings.co2_g;
    mockStats.model_usage[result.selected_model] = (mockStats.model_usage[result.selected_model] || 0) + 1;
    mockStats.average_model = Object.entries(mockStats.model_usage).sort((a,b) => b[1]-a[1])[0]?.[0] || "N/A";
    const totalCo2 = mockStats.total_co2_saved_g;
    mockStats.co2_equivalents = {
      car_km: parseFloat((totalCo2 / 120).toFixed(4)),
      pine_trees_days: parseFloat((totalCo2 / (5000/365)).toFixed(4)),
      phone_charges: parseFloat((totalCo2 / 8.22).toFixed(4)),
    };
    return result;
  }

  const res = await fetch(`${API_BASE}/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, policy }),
  });
  return res.json();
}

export async function getStats() {
  if (USE_MOCK) {
    return mockStats;
  }
  const res = await fetch(`${API_BASE}/stats`);
  return res.json();
}

export async function getModels() {
  if (USE_MOCK) {
    return MOCK_MODELS;
  }
  const res = await fetch(`${API_BASE}/models`);
  return res.json();
}

export async function getPolicies() {
  if (USE_MOCK) {
    return {
      cost_first: { label: "비용 우선", description: "비용 절감을 최우선으로 합니다." },
      carbon_first: { label: "탄소 우선", description: "CO₂ 배출 최소화를 최우선으로 합니다." },
      quality_first: { label: "품질 우선", description: "응답 품질을 최우선으로 합니다." },
      balanced: { label: "균형", description: "비용, 탄소, 품질을 균형 있게 고려합니다." },
    };
  }
  const res = await fetch(`${API_BASE}/policies`);
  return res.json();
}
