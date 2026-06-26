import React from 'react'
import './Sidebar.css'

function Sidebar({ stats, lastResult, policy, onPolicyChange }) {
  const policies = [
    { key: 'cost_first', label: '💰 비용 우선', desc: '비용 절감 최우선' },
    { key: 'carbon_first', label: '🌱 탄소 우선', desc: 'CO₂ 최소화' },
    { key: 'quality_first', label: '⭐ 품질 우선', desc: '응답 품질 최우선' },
    { key: 'balanced', label: '⚖️ 균형', desc: '비용·탄소·품질 균형' },
  ]

  return (
    <aside className="sidebar">
      {/* 오늘 절감량 */}
      <section className="sidebar-section">
        <h3 className="section-title">오늘 절감량</h3>
        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-value">${stats?.total_cost_saved_usd?.toFixed(4) || '0.0000'}</span>
            <span className="stat-label">비용 절감</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats?.total_co2_saved_g?.toFixed(3) || '0.000'}g</span>
            <span className="stat-label">CO₂ 절감</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats?.total_requests_today || 0}</span>
            <span className="stat-label">요청 수</span>
          </div>
        </div>
      </section>

      {/* 운영 정책 */}
      <section className="sidebar-section">
        <h3 className="section-title">운영 정책</h3>
        <div className="policy-list">
          {policies.map(p => (
            <button
              key={p.key}
              className={`policy-btn ${policy === p.key ? 'active' : ''}`}
              onClick={() => onPolicyChange(p.key)}
            >
              <span className="policy-label">{p.label}</span>
              <span className="policy-desc">{p.desc}</span>
            </button>
          ))}
        </div>
      </section>

      {/* 추천 모델 정보 */}
      {lastResult && (
        <section className="sidebar-section">
          <h3 className="section-title">최근 추천</h3>
          <div className="recent-model">
            <div className="model-badge">{lastResult.selected_model}</div>
            <div className="model-meta">
              <span>작업: {lastResult.task_type}</span>
              <span>난이도: {lastResult.difficulty}</span>
            </div>
          </div>
        </section>
      )}

      {/* 모델별 적합도 */}
      <section className="sidebar-section">
        <h3 className="section-title">모델 사용 비율</h3>
        <div className="model-usage">
          {stats?.model_usage && Object.keys(stats.model_usage).length > 0 ? (
            Object.entries(stats.model_usage)
              .sort((a, b) => b[1] - a[1])
              .map(([model, count]) => {
                const total = stats.total_requests_today || 1
                const pct = ((count / total) * 100).toFixed(0)
                return (
                  <div key={model} className="usage-row">
                    <span className="usage-model">{model}</span>
                    <div className="usage-bar-container">
                      <div className="usage-bar" style={{ width: `${pct}%` }}></div>
                    </div>
                    <span className="usage-pct">{pct}%</span>
                  </div>
                )
              })
          ) : (
            <p className="empty-text">아직 요청이 없습니다</p>
          )}
        </div>
      </section>
    </aside>
  )
}

export default Sidebar
