import React from 'react'
import './Dashboard.css'

function Dashboard({ stats }) {
  if (!stats) {
    return (
      <div className="dashboard">
        <div className="dash-empty">데이터를 불러오는 중...</div>
      </div>
    )
  }

  const {
    total_requests_today,
    total_cost_saved_usd,
    total_co2_saved_g,
    model_usage,
    average_model,
    co2_equivalents,
  } = stats

  const totalUsage = Object.values(model_usage || {}).reduce((a, b) => a + b, 0)

  return (
    <div className="dashboard">
      <h2 className="dash-title">관리자 대시보드</h2>

      {/* 핵심 지표 */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <span className="kpi-icon">📋</span>
          <span className="kpi-value">{total_requests_today}</span>
          <span className="kpi-label">오늘 요청 수</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-icon">💰</span>
          <span className="kpi-value">${total_cost_saved_usd?.toFixed(4)}</span>
          <span className="kpi-label">총 절감 비용</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-icon">🌍</span>
          <span className="kpi-value">{total_co2_saved_g?.toFixed(4)}g</span>
          <span className="kpi-label">총 절감 CO₂</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-icon">🤖</span>
          <span className="kpi-value">{average_model}</span>
          <span className="kpi-label">최다 추천 모델</span>
        </div>
      </div>

      {/* 모델별 사용 비율 */}
      <div className="dash-section">
        <h3 className="dash-section-title">모델별 사용 비율</h3>
        <div className="usage-chart">
          {model_usage && Object.keys(model_usage).length > 0 ? (
            Object.entries(model_usage)
              .sort((a, b) => b[1] - a[1])
              .map(([model, count]) => {
                const pct = totalUsage > 0 ? ((count / totalUsage) * 100).toFixed(1) : 0
                return (
                  <div key={model} className="chart-row">
                    <span className="chart-model">{model}</span>
                    <div className="chart-bar-container">
                      <div 
                        className="chart-bar" 
                        style={{ width: `${pct}%` }}
                      ></div>
                    </div>
                    <span className="chart-value">{count}회 ({pct}%)</span>
                  </div>
                )
              })
          ) : (
            <p className="dash-empty-text">아직 요청 데이터가 없습니다</p>
          )}
        </div>
      </div>

      {/* CO₂ 환산 */}
      <div className="dash-section">
        <h3 className="dash-section-title">CO₂ 절감 환산</h3>
        <div className="equiv-grid">
          <div className="equiv-card">
            <span className="equiv-icon">🚗</span>
            <span className="equiv-value">{co2_equivalents?.car_km?.toFixed(4)} km</span>
            <span className="equiv-label">자동차 주행 거리</span>
          </div>
          <div className="equiv-card">
            <span className="equiv-icon">🌲</span>
            <span className="equiv-value">{co2_equivalents?.pine_trees_days?.toFixed(4)} 일</span>
            <span className="equiv-label">소나무 1그루 흡수량</span>
          </div>
          <div className="equiv-card">
            <span className="equiv-icon">📱</span>
            <span className="equiv-value">{co2_equivalents?.phone_charges?.toFixed(4)} 회</span>
            <span className="equiv-label">스마트폰 충전 횟수</span>
          </div>
        </div>
      </div>

      {/* 안내 */}
      <div className="dash-notice">
        <p>
          💡 이 대시보드는 ECOROUTE가 단일 고성능 모델(Claude Sonnet) 대비 
          얼마나 비용과 탄소를 절감했는지 보여줍니다.
          실제 API 연동 후에는 실시간 데이터가 반영됩니다.
        </p>
      </div>
    </div>
  )
}

export default Dashboard
