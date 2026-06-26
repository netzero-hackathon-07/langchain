import React from 'react'
import './Header.css'

function Header({ onToggleDashboard, showDashboard }) {
  return (
    <header className="header">
      <div className="header-left">
        <div className="logo">
          <span className="logo-icon">🌿</span>
          <h1 className="logo-text">ECOROUTE</h1>
        </div>
        <span className="status-badge">
          <span className="status-dot"></span>
          Online
        </span>
      </div>
      <div className="header-right">
        <button 
          className={`nav-btn ${!showDashboard ? 'active' : ''}`}
          onClick={() => showDashboard && onToggleDashboard()}
        >
          라우터
        </button>
        <button 
          className={`nav-btn ${showDashboard ? 'active' : ''}`}
          onClick={() => !showDashboard && onToggleDashboard()}
        >
          대시보드
        </button>
      </div>
    </header>
  )
}

export default Header
