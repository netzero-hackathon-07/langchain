import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import MainPanel from './components/MainPanel'
import Dashboard from './components/Dashboard'
import { getStats } from './api'
import './App.css'

function App() {
  const [stats, setStats] = useState(null)
  const [lastResult, setLastResult] = useState(null)
  const [policy, setPolicy] = useState('balanced')
  const [showDashboard, setShowDashboard] = useState(false)

  const refreshStats = async () => {
    const data = await getStats()
    setStats(data)
  }

  useEffect(() => {
    refreshStats()
  }, [])

  const handleRouteComplete = (result) => {
    setLastResult(result)
    refreshStats()
  }

  return (
    <div className="app">
      <Header 
        onToggleDashboard={() => setShowDashboard(!showDashboard)} 
        showDashboard={showDashboard}
      />
      
      {showDashboard ? (
        <Dashboard stats={stats} />
      ) : (
        <div className="app-body">
          <Sidebar 
            stats={stats} 
            lastResult={lastResult}
            policy={policy}
            onPolicyChange={setPolicy}
          />
          <MainPanel 
            policy={policy}
            onRouteComplete={handleRouteComplete}
          />
        </div>
      )}
    </div>
  )
}

export default App
