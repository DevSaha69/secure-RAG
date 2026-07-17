import { useState } from 'react'
import { uploadPDF, queryRAG } from '../api/client'

export default function QueryPanel({ 
  activeCollection, 
  onCollectionsChange, 
  includeLlm, 
  defenseEnabled, 
  fetchHealth 
}) {
  const [strategy, setStrategy] = useState('mmr')
  const [query, setQuery] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploadMode, setUploadMode] = useState('current') // 'current' | 'new'
  const [newCollectionName, setNewCollectionName] = useState('')

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    const targetCollection = uploadMode === 'current' 
      ? activeCollection 
      : newCollectionName.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '') || 'custom_collection'

    setUploadStatus(`Uploading and indexing to "${targetCollection}"...`)
    try {
      const { data } = await uploadPDF(file, targetCollection)
      setUploadStatus(`✅ Successfully indexed ${data.chunks_stored} chunks into "${data.collection}"`)
      if (uploadMode === 'new') {
        setNewCollectionName('')
        setUploadMode('current')
      }
      if (onCollectionsChange) {
        onCollectionsChange(uploadMode === 'new')
      }
      fetchHealth()
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || 'Error uploading document. Please check server logs.';
      setUploadStatus(`❌ ${errorMsg}`)
    }
  }

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    const currentQuery = query
    setQuery('') // Clear input box for next query
    try {
      const { data } = await queryRAG(currentQuery, strategy, 3, activeCollection, includeLlm, defenseEnabled)
      const newLog = {
        id: Date.now(),
        query: currentQuery,
        answer: data.answer,
        chunks: data.chunks || [],
        scores: data.scores || [],
        timeMs: data.time_ms || 0,
        strategyUsed: strategy,
        llmWasIncluded: data.include_llm ?? true,
        defenseEnabled: defenseEnabled
      }
      setHistory(prev => [newLog, ...prev])
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || 'Error fetching answer. Make sure backend is running.';
      const newLog = {
        id: Date.now(),
        query: currentQuery,
        answer: `❌ ${errorMsg}`,
        chunks: [],
        scores: [],
        timeMs: 0,
        strategyUsed: strategy,
        llmWasIncluded: includeLlm,
        defenseEnabled: defenseEnabled
      }
      setHistory(prev => [newLog, ...prev])
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = () => {
    setHistory([])
  }

  return (
    <>
      {/* Upload Zone */}
      <div className="section-card">
        <h2 className="section-title">
          <span className="material-symbols-outlined">library_add</span>
          Document Ingestion
        </h2>
        
        {/* Upload Mode Selector */}
        <div className="upload-options-container">
          <label className="upload-option-label">
            <input 
              type="radio" 
              name="uploadMode" 
              value="current"
              checked={uploadMode === 'current'}
              onChange={() => setUploadMode('current')}
            />
            <span>Ingest into active collection (<strong>{activeCollection}</strong>)</span>
          </label>
          <label className="upload-option-label">
            <input 
              type="radio" 
              name="uploadMode" 
              value="new"
              checked={uploadMode === 'new'}
              onChange={() => setUploadMode('new')}
            />
            <span>Create new collection</span>
          </label>
        </div>

        {uploadMode === 'new' && (
          <div className="new-collection-input-wrapper">
            <input 
              type="text" 
              className="chat-input"
              style={{ marginBottom: '13.2px' }}
              placeholder="Enter new collection name (lowercase, numbers, _ or - only)..."
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ''))}
            />
          </div>
        )}

        <label className={`upload-zone ${uploadMode === 'new' && !newCollectionName.trim() ? 'disabled' : ''}`}>
          <span className="material-symbols-outlined upload-icon">cloud_upload</span>
          <div className="upload-label">
            {uploadMode === 'new' && !newCollectionName.trim() ? (
              <span style={{ color: 'var(--warning)', fontWeight: 'bold' }}>Please enter a collection name above first</span>
            ) : (
              <span>Click to select a PDF and parse it into <strong>{uploadMode === 'current' ? activeCollection : newCollectionName}</strong></span>
            )}
          </div>
          <input 
            type="file" 
            accept=".pdf" 
            className="upload-input" 
            onChange={handleUpload} 
            disabled={uploadMode === 'new' && !newCollectionName.trim()}
          />
        </label>
        {uploadStatus && (
          <div className="upload-status" style={{ color: uploadStatus.includes('Successfully') ? 'var(--success)' : uploadStatus.includes('Uploading') ? 'var(--accent)' : 'var(--danger)' }}>
            {uploadStatus}
          </div>
        )}
      </div>

      {/* Retrieval Strategy Selector */}
      <div className="section-card">
        <h2 className="section-title">
          <span className="material-symbols-outlined">filter_alt</span>
          Retrieval Algorithm
        </h2>
        <div className="strategy-container">
          {[
            { id: 'topk', name: 'Top-K Vector' },
            { id: 'bm25', name: 'BM25 Keyword' },
            { id: 'hybrid', name: 'Hybrid (RRF)' },
            { id: 'mmr', name: 'MMR Diverse' },
          ].map((s) => (
            <button
              key={s.id}
              onClick={() => setStrategy(s.id)}
              className={`strategy-pill ${strategy === s.id ? 'active' : ''}`}
            >
              {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Query Search Bar */}
      <div className="section-card">
        <h2 className="section-title">
          <span className="material-symbols-outlined">question_answer</span>
          Ask the Database
        </h2>
        <div className="chat-input-wrapper">
          <input
            className="chat-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && handleQuery()}
            placeholder="Search documents or query the LLM..."
            disabled={loading}
          />
          <button 
            className="chat-button" 
            onClick={handleQuery} 
            disabled={loading || !query.trim()}
          >
            <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
              {loading ? 'sync' : 'search'}
            </span>
            {loading ? 'Querying...' : includeLlm ? 'Ask' : 'Retrieve'}
          </button>
        </div>
      </div>

      {/* Question History Stream */}
      <div className="query-history-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="section-title" style={{ margin: 0 }}>
            <span className="material-symbols-outlined">history</span>
            Query Execution Logs
          </h3>
          {history.length > 0 && (
            <button 
              onClick={clearHistory}
              className="delete-collection-btn" 
              style={{ padding: '4px 10px', fontSize: '11px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>clear_all</span>
              Clear Logs
            </button>
          )}
        </div>

        {history.length === 0 ? (
          <div className="section-card" style={{ textAlign: 'center', padding: '33px', borderStyle: 'dashed' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '36px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              explore
            </span>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
              No query logs registered yet. Type a query above and hit Search to analyze retrieval results.
            </p>
          </div>
        ) : (
          history.map((log) => (
            <div key={log.id} className="query-log-item">
              {/* Log Item Header */}
              <div className="query-log-header">
                <span className="query-log-question" title={log.query}>
                  Query: "{log.query}"
                </span>
                <span className="query-meta-badge" style={{ color: 'var(--text-secondary)' }}>
                  {new Date(log.id).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              </div>

              {/* Log Item Body */}
              <div className="query-log-body">
                {log.llmWasIncluded ? (
                  <p style={{ color: 'var(--text-main)', margin: 0, whiteSpace: 'pre-wrap' }}>
                    {log.answer}
                  </p>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)' }}>
                    <span className="material-symbols-outlined" style={{ color: 'var(--accent)' }}>info</span>
                    <span>
                      LLM generation bypassed. Displaying raw semantic retrieval results.
                    </span>
                  </div>
                )}
              </div>

              {/* Metadata Badges */}
              <div className="query-log-meta">
                <span className="query-meta-badge">
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>analytics</span>
                  Algorithm: <strong style={{ textTransform: 'uppercase' }}>{log.strategyUsed}</strong>
                </span>
                <span className="query-meta-badge">
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>schedule</span>
                  Latency: <strong>{log.timeMs.toFixed(1)} ms</strong>
                </span>
                <span className="query-meta-badge">
                  <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>layers</span>
                  Sources: <strong>{log.chunks.length} chunks</strong>
                </span>
                {log.defenseEnabled && (
                  <span className="query-meta-badge" style={{ color: 'var(--success)' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '14px', color: 'var(--success)' }}>shield</span>
                    Shield Active
                  </span>
                )}
              </div>

              {/* Context Drawer */}
              {log.chunks.length > 0 && (
                <details className="chunks-details">
                  <summary className="chunks-summary">
                    <span>Show Retrieved Context Sources ({log.chunks.length})</span>
                    <span className="material-symbols-outlined">expand_more</span>
                  </summary>
                  <div style={{ backgroundColor: 'rgba(0,0,0,0.15)' }}>
                    {log.chunks.map((chunk, idx) => (
                      <div key={idx} className="chunk-item">
                        <div className="chunk-header">
                          Source Chunk #{idx + 1} {log.scores[idx] !== undefined && `(Distance Score: ${log.scores[idx].toFixed(4)})`}
                        </div>
                        <div style={{ color: 'var(--text-main)', fontStyle: 'normal' }}>
                          "{chunk}"
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ))
        )}
      </div>
    </>
  )
}
