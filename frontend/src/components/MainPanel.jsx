import React, { useState } from 'react'
import ResultCard from './ResultCard'
import { routeQuery } from '../api'
import './MainPanel.css'

const EXAMPLE_QUERIES = [
  "이 이메일 문장을 자연스럽게 고쳐줘",
  "이 코드를 리팩토링해줘",
  "AWS 3-tier 아키텍처를 설계해줘",
  "블록체인의 개념을 설명해줘",
  "이 보고서를 3줄로 요약해줘",
  "이 문장을 영어로 번역해줘",
]

function MainPanel({ policy, onRouteComplete }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState([])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const data = await routeQuery(query.trim(), policy)
      setResult(data)
      setHistory(prev => [data, ...prev].slice(0, 5))
      onRouteComplete(data)
    } catch (err) {
      console.error('Route error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleExample = (q) => {
    setQuery(q)
  }

  return (
    <main className="main-panel">
      {/* 입력 영역 */}
      <section className="input-section">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <textarea
              className="query-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="AI에게 보낼 요청을 입력하세요..."
              rows={3}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            <button 
              type="submit" 
              className="submit-btn" 
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <span className="spinner"></span>
              ) : (
                '라우팅 분석'
              )}
            </button>
          </div>
        </form>

        {/* 예시 쿼리 */}
        <div className="examples">
          <span className="examples-label">예시:</span>
          <div className="examples-list">
            {EXAMPLE_QUERIES.map((q, i) => (
              <button 
                key={i} 
                className="example-chip"
                onClick={() => handleExample(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 결과 영역 */}
      <section className="result-section">
        {result ? (
          <ResultCard result={result} />
        ) : (
          <div className="empty-state">
            <div className="empty-icon">🌿</div>
            <h3>ECOROUTE에 오신 것을 환영합니다</h3>
            <p>요청을 입력하면 최적의 AI 모델을 추천하고<br/>비용·탄소 절감량을 계산합니다.</p>
          </div>
        )}
      </section>

      {/* 히스토리 */}
      {history.length > 1 && (
        <section className="history-section">
          <h3 className="section-title">이전 결과</h3>
          <div className="history-list">
            {history.slice(1).map((item, i) => (
              <div key={i} className="history-item">
                <span className="history-query">{item.query.slice(0, 40)}...</span>
                <span className="history-model">{item.selected_model}</span>
                <span className="history-saving">-{item.savings.percent_less_co2}% CO₂</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}

export default MainPanel
