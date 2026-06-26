import React from 'react'
import './ResultCard.css'

function ResultCard({ result }) {
  if (!result) return null

  const { 
    selected_model, task_type, difficulty, reason, 
    estimated_tokens, savings, alternatives, baseline_model 
  } = result

  const difficultyColor = {
    low: '#22c55e',
    medium: '#eab308',
    high: '#ef4444',
  }

  return (
    <div className="result-card">
      {/* 헤더 */}
      <div className="result-header">
        <div className="result-model">
          <span className="model-label">추천 모델</span>
          <h2 className="model-name">{selected_model}</h2>
        </div>
        <div className="result-tags">
          <span className="tag task-tag">{task_type}</span>
          <span 
            className="tag diff-tag" 
            style={{ '--tag-color': difficultyColor[difficulty] }}
          >
            {difficulty}
          </span>
        </div>
      </div>

      {/* 추천 이유 */}
      <div className="result-reason">
        <p>{reason}</p>
      </div>

      {/* 절감 지표 */}
      <div className="savings-grid">
        <div className="saving-card cost">
          <span className="saving-icon">💰</span>
          <div className="saving-info">
            <span className="saving-value">-{savings.percent_cheaper}%</span>
            <span className="saving-detail">${savings.cost_usd.toFixed(5)} 절감</span>
            <span className="saving-label">비용 절감</span>
          </div>
        </div>
        <div className="saving-card co2">
          <span className="saving-icon">🌍</span>
          <div className="saving-info">
            <span className="saving-value">-{savings.percent_less_co2}%</span>
            <span className="saving-detail">{savings.co2_g.toFixed(4)}g 절감</span>
            <span className="saving-label">CO₂ 절감</span>
          </div>
        </div>
        <div className="saving-card token">
          <span className="saving-icon">📊</span>
          <div className="saving-info">
            <span className="saving-value">{estimated_tokens.total}</span>
            <span className="saving-detail">입력 {estimated_tokens.input} + 출력 {estimated_tokens.output}</span>
            <span className="saving-label">예상 토큰</span>
          </div>
        </div>
      </div>

      {/* 하단 정보 */}
      <div className="result-footer">
        <div className="footer-item">
          <span className="footer-label">기준 모델</span>
          <span className="footer-value">{baseline_model}</span>
        </div>
        <div className="footer-item">
          <span className="footer-label">대체 모델</span>
          <span className="footer-value">{alternatives.join(', ')}</span>
        </div>
      </div>
    </div>
  )
}

export default ResultCard
