import { useState, useEffect } from 'react'
import QueryPanel from './components/QueryPanel'
import AttackPanel from './components/AttackPanel'
import { getCollections, deleteCollection, getCollectionHealth } from './api/client'
import './App.css'

export default function App() {
  const [mode, setMode] = useState('query') // 'query' | 'attack'
  const [activeCollection, setActiveCollection] = useState('gpt2_paper')
  const [collections, setCollections] = useState(['gpt2_paper'])
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)
  
  // Settings relocated to global sidebar control panel
  const [includeLlm, setIncludeLlm] = useState(true)
  const [defenseEnabled, setDefenseEnabled] = useState(false)
  const [health, setHealth] = useState(null)

  const loadCollections = async (selectNewest = false) => {
    try {
      const { data } = await getCollections()
      setCollections(data.collections)
      
      if (data.collections.length > 0) {
        if (selectNewest) {
          setActiveCollection(data.collections[data.collections.length - 1])
        } else if (!data.collections.includes(activeCollection)) {
          setActiveCollection(data.collections[0])
        }
      }
    } catch (err) {
      console.error('Error fetching collections:', err)
    }
  }

  const fetchHealth = async () => {
    if (!activeCollection) return
    try {
      const { data } = await getCollectionHealth(activeCollection)
      setHealth(data)
    } catch (err) {
      console.error('Error fetching collection health:', err)
    }
  }

  useEffect(() => {
    loadCollections()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    fetchHealth()
    setIsConfirmingDelete(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCollection])

  const handleDeleteCollection = async () => {
    if (activeCollection === 'gpt2_paper') return
    if (!isConfirmingDelete) {
      setIsConfirmingDelete(true)
      return
    }
    try {
      await deleteCollection(activeCollection)
      await loadCollections()
      setIsConfirmingDelete(false)
    } catch (err) {
      console.error('Error deleting collection:', err)
      alert(err.response?.data?.detail || 'Failed to delete collection')
      setIsConfirmingDelete(false)
    }
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar Control Panel */}
      <aside className="sidebar">
        <div className="brand-header">
          <h1 className="brand-title">
            <span className="material-symbols-outlined">shield_lock</span>
            Secure-RAG
          </h1>
          <p className="brand-subtitle">
            Attack Simulation & Defense on Retrieval-Augmented Generation Systems
          </p>
        </div>

        {/* Target Collection Card */}
        <div className="section-card">
          <h2 className="section-title">
            <span className="material-symbols-outlined">database</span>
            Database Target
          </h2>
          <label htmlFor="collection-select" className="dropdown-label">
            Select Active Collection:
          </label>
          <select
            id="collection-select"
            value={activeCollection}
            onChange={(e) => setActiveCollection(e.target.value)}
            className="custom-select"
            style={{ marginBottom: '12.5px' }}
          >
            {collections.map((col) => (
              <option key={col} value={col}>
                {col === 'gpt2_paper' ? 'gpt2_paper (Default)' : col}
              </option>
            ))}
          </select>
          {activeCollection !== 'gpt2_paper' && (
            <button
              onClick={handleDeleteCollection}
              className={`delete-collection-btn ${isConfirmingDelete ? 'confirming' : ''}`}
              style={{ width: '100%', justifyContent: 'center' }}
              title="Delete this collection permanently"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>delete</span>
              {isConfirmingDelete ? 'Confirm Delete?' : 'Delete Collection'}
            </button>
          )}
        </div>

        {/* Collection Health Indicators */}
        {health && (
          <div className={`health-card ${health.alert ? 'alert' : 'healthy'}`}>
            <div className="health-header">
              <span className="health-label">System Health Score</span>
              <strong className={`health-score ${health.alert ? 'danger-text' : 'success-text'}`}>
                {health.health_score}%
              </strong>
            </div>
            <div className="health-details">
              {health.alert ? (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: 'var(--danger)' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px', marginTop: '2px' }}>warning</span>
                  <span>
                    <strong>Poison Alert!</strong> {health.poison_chunks} of {health.total_chunks} total chunks detected as poisoned.
                  </span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', color: 'var(--success)' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px', marginTop: '2px' }}>verified_user</span>
                  <span>
                    <strong>Healthy.</strong> {health.legitimate_chunks} chunks loaded. Cosine anomalies within acceptable range.
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Global Pipeline Configurations */}
        <div className="section-card">
          <h2 className="section-title">
            <span className="material-symbols-outlined">settings_input_component</span>
            Pipeline Shield
          </h2>
          
          <div className="sidebar-settings-panel">
            {/* LLM Toggle switch */}
            <div 
              className="sidebar-setting-row"
              onClick={() => setIncludeLlm(!includeLlm)}
              title="Include LLM answer generation in pipelines"
            >
              <div className="setting-details">
                <span className="setting-title-text">
                  <span className="material-symbols-outlined" style={{ color: 'var(--accent)', fontSize: '18px' }}>psychology</span>
                  Gemini Generation
                </span>
                <span className="setting-desc-text">
                  {includeLlm ? 'Full LLM responses' : 'Raw retrieval vector logs'}
                </span>
              </div>
              <div className={`switch-container ${includeLlm ? 'active-accent' : ''}`}>
                <div className="switch-dot" />
              </div>
            </div>

            {/* RAG Shield toggle switch */}
            <div 
              className="sidebar-setting-row"
              onClick={() => setDefenseEnabled(!defenseEnabled)}
              title="Toggle input prompt sanitation and context filtering defenses"
            >
              <div className="setting-details">
                <span className="setting-title-text">
                  <span className="material-symbols-outlined" style={{ color: 'var(--success)', fontSize: '18px' }}>shield</span>
                  Active RAG Shield
                </span>
                <span className="setting-desc-text">
                  {defenseEnabled ? 'Sanitizer Active' : 'Defense Filter Off'}
                </span>
              </div>
              <div className={`switch-container ${defenseEnabled ? 'active' : ''}`}>
                <div className="switch-dot" />
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Workspace Column */}
      <main className="workspace">
        {/* Navigation Tabs */}
        <div className="dashboard-tabs">
          <button 
            className={`tab-btn ${mode === 'query' ? 'active' : ''}`}
            onClick={() => setMode('query')}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>search</span>
            Search & Query Mode
          </button>
          <button 
            className={`tab-btn ${mode === 'attack' ? 'active' : ''}`}
            onClick={() => setMode('attack')}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>coronavirus</span>
            Adversarial Simulation
          </button>
        </div>

        {mode === 'query' && (
          <QueryPanel 
            activeCollection={activeCollection} 
            onCollectionsChange={loadCollections} 
            includeLlm={includeLlm}
            defenseEnabled={defenseEnabled}
            health={health}
            fetchHealth={fetchHealth}
          />
        )}
        {mode === 'attack' && (
          <AttackPanel 
            activeCollection={activeCollection} 
            globalIncludeLlm={includeLlm}
          />
        )}
      </main>
    </div>
  )
}
