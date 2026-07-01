import { useState, useEffect } from 'react'
import QueryPanel from './components/QueryPanel'
import AttackPanel from './components/AttackPanel'
import { getCollections, deleteCollection } from './api/client'
import './App.css'

export default function App() {
  const [mode, setMode] = useState('query') // 'query' | 'attack'
  const [activeCollection, setActiveCollection] = useState('gpt2_paper')
  const [collections, setCollections] = useState(['gpt2_paper'])
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)

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

  useEffect(() => {
    loadCollections()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setIsConfirmingDelete(false)
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
    <div className="dashboard-container">
      <h1 className="app-title">⚔ SECURE RAG</h1>
      <p className="app-subtitle">A Security-Focused Retrieval-Augmented Generation Platform</p>

      {/* Global Collection Selector Banner */}
      <div className="collection-selector-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
          <label htmlFor="collection-select" className="collection-label">
            Target Collection:
          </label>
          <select
            id="collection-select"
            value={activeCollection}
            onChange={(e) => setActiveCollection(e.target.value)}
            className="collection-dropdown"
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
              title="Delete this collection permanently"
            >
              {isConfirmingDelete ? '⚠️ Confirm Delete?' : '🗑️ Delete Collection'}
            </button>
          )}
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="dashboard-tabs">
        <button 
          className={`tab-btn ${mode === 'query' ? 'active' : ''}`}
          onClick={() => setMode('query')}
        >
          🔍 Query Mode
        </button>
        <button 
          className={`tab-btn ${mode === 'attack' ? 'active' : ''}`}
          onClick={() => setMode('attack')}
        >
          ⚔ Attack Simulation
        </button>
      </div>

      {mode === 'query' && (
        <QueryPanel 
          activeCollection={activeCollection} 
          onCollectionsChange={loadCollections} 
        />
      )}
      {mode === 'attack' && (
        <AttackPanel 
          activeCollection={activeCollection} 
        />
      )}
    </div>
  )
}
