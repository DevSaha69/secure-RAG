import { useState, useEffect } from 'react'
import { uploadPDF, queryRAG, getCollectionHealth } from '../api/client'

export default function QueryPanel({ activeCollection, onCollectionsChange }) {
  const [strategy, setStrategy] = useState('mmr')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState(null)
  const [chunks, setChunks] = useState([])
  const [scores, setScores] = useState([])
  const [timeMs, setTimeMs] = useState(0)
  const [includeLlm, setIncludeLlm] = useState(true)
  const [llmWasIncluded, setLlmWasIncluded] = useState(true)
  const [defenseEnabled, setDefenseEnabled] = useState(false)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploadMode, setUploadMode] = useState('current') // 'current' | 'new'
  const [newCollectionName, setNewCollectionName] = useState('')
  const [hasResult, setHasResult] = useState(false)

  const fetchHealth = async () => {
    if (!activeCollection) return
    try {
      const { data } = await getCollectionHealth(activeCollection)
      setHealth(data)
    } catch (err) {
      console.error('Error fetching collection health:', err)
    }
  }

  // Fetch health stats when activeCollection changes
  useEffect(() => {
    fetchHealth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCollection])

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
    setAnswer(null)
    setChunks([])
    setScores([])
    setHasResult(false)
    try {
      const { data } = await queryRAG(query, strategy, 3, activeCollection, includeLlm, defenseEnabled)
      setAnswer(data.answer)
      setChunks(data.chunks || [])
      setScores(data.scores || [])
      setTimeMs(data.time_ms || 0)
      setLlmWasIncluded(data.include_llm ?? true)
      setHasResult(true)
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || 'Error fetching answer. Make sure backend is running.';
      setAnswer(`❌ ${errorMsg}`)
      setHasResult(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Collection Health Indicator */}
      {health && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          background: health.alert ? 'rgba(239, 68, 68, 0.08)' : 'rgba(16, 185, 129, 0.05)',
          border: `1px solid ${health.alert ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.15)'}`,
          fontSize: '13px',
          color: health.alert ? '#f87171' : '#10b981',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{health.alert ? '⚠️' : '🛡️'}</span>
            <span>
              {health.alert ? (
                <strong>Poison Alert: {health.poison_chunks} poisoned / {health.total_chunks} total chunks indexed.</strong>
              ) : (
                <span>Knowledge base healthy: <strong>{health.legitimate_chunks}</strong> legitimate chunks indexed.</span>
              )}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', opacity: 0.8 }}>Health:</span>
            <strong style={{ fontSize: '14px', color: health.alert ? '#ef4444' : '#10b981' }}>{health.health_score}%</strong>
          </div>
        </div>
      )}

      {/* Upload Zone */}
      <div className="section-card">
        <h2 className="section-title">Knowledge Base Ingestion</h2>
        
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
            <span>Upload to active collection (<strong>{activeCollection}</strong>)</span>
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
              style={{ padding: '10px 14px', fontSize: '13px', marginBlock: '10px 15px', width: '100%' }}
              placeholder="Enter new collection name (lowercase, numbers, _ or - only)..."
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ''))}
            />
          </div>
        )}

        <label className={`upload-zone ${uploadMode === 'new' && !newCollectionName.trim() ? 'disabled' : ''}`}>
          <div className="upload-icon">📂</div>
          <div className="upload-label">
            {uploadMode === 'new' && !newCollectionName.trim() ? (
              <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>Please enter a collection name above first</span>
            ) : (
              <span>Click to upload a PDF and index it in <strong>{uploadMode === 'current' ? activeCollection : newCollectionName}</strong></span>
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
        {uploadStatus && <div className="upload-status">{uploadStatus}</div>}
      </div>

      {/* Retrieval Configuration */}
      <div className="section-card">
        <h2 className="section-title">Retrieval Strategy</h2>
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

      {/* LLM & Defense Configuration Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBlock: '16px' }}>
        {/* LLM Toggle */}
        <div className="section-card" style={{ padding: '14px', margin: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
            onClick={() => setIncludeLlm(!includeLlm)}
          >
            <div
              style={{
                width: '40px',
                height: '22px',
                borderRadius: '11px',
                background: includeLlm
                  ? 'linear-gradient(135deg, #c084fc, #6366f1)'
                  : 'rgba(255, 255, 255, 0.1)',
                position: 'relative',
                transition: 'all 0.3s ease',
                flexShrink: 0,
                boxShadow: includeLlm ? '0 0 10px rgba(192, 132, 252, 0.3)' : 'none',
              }}
            >
              <div
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: '#fff',
                  position: 'absolute',
                  top: '3px',
                  left: includeLlm ? '21px' : '3px',
                  transition: 'left 0.3s ease',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                }}
              />
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: includeLlm ? '#e5e7eb' : '#6b7280' }}>
                Gemini LLM
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                {includeLlm ? 'LLM Generation active' : 'Retrieval only'}
              </div>
            </div>
          </div>
        </div>

        {/* Defense Toggle */}
        <div className="section-card" style={{ padding: '14px', margin: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
              userSelect: 'none',
            }}
            onClick={() => setDefenseEnabled(!defenseEnabled)}
          >
            <div
              style={{
                width: '40px',
                height: '22px',
                borderRadius: '11px',
                background: defenseEnabled
                  ? 'linear-gradient(135deg, #10b981, #047857)'
                  : 'rgba(255, 255, 255, 0.1)',
                position: 'relative',
                transition: 'all 0.3s ease',
                flexShrink: 0,
                boxShadow: defenseEnabled ? '0 0 10px rgba(16, 185, 129, 0.3)' : 'none',
              }}
            >
              <div
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: '#fff',
                  position: 'absolute',
                  top: '3px',
                  left: defenseEnabled ? '21px' : '3px',
                  transition: 'left 0.3s ease',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                }}
              />
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: defenseEnabled ? '#e5e7eb' : '#6b7280' }}>
                RAG Shield
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>
                {defenseEnabled ? '🛡️ Shield Active' : '⚠️ Shield Off'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Query Interface */}
      <div className="section-card">
        <h2 className="section-title">Ask the Knowledge Base</h2>
        <div className="chat-input-wrapper">
          <input
            className="chat-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !loading && handleQuery()}
            placeholder="Search documents or ask a question..."
            disabled={loading}
          />
          <button 
            className="chat-button" 
            onClick={handleQuery} 
            disabled={loading || !query.trim()}
          >
            {loading ? 'Thinking...' : includeLlm ? 'Ask' : 'Retrieve'}
          </button>
        </div>
      </div>

      {/* Generated Response or Retrieval-Only Notice */}
      {hasResult && (
        <div className="result-card">
          {llmWasIncluded && answer ? (
            <>
              <div className="result-title">Response</div>
              <div className="result-text">{answer}</div>
            </>
          ) : answer && answer.startsWith('❌') ? (
            <>
              <div className="result-title">Error</div>
              <div className="result-text">{answer}</div>
            </>
          ) : (
            <>
              <div className="result-title" style={{ color: '#c084fc' }}>⚡ Retrieval Only</div>
              <div style={{ padding: '12px', background: 'rgba(192, 132, 252, 0.06)', border: '1px dashed rgba(192, 132, 252, 0.2)', borderRadius: '6px' }}>
                <span style={{ color: '#9ca3af', fontSize: '14px' }}>
                  LLM generation was skipped. Showing retrieved chunks and relevance scores below.
                </span>
              </div>
            </>
          )}
          
          <div className="meta-info">
            <div className="meta-item">
              <span>Strategy:</span> 
              <strong style={{ color: '#c084fc', textTransform: 'uppercase' }}>{strategy}</strong>
            </div>
            <div className="meta-item">
              <span>Latency:</span> 
              <strong style={{ color: '#38bdf8' }}>{timeMs.toFixed(1)} ms</strong>
            </div>
            <div className="meta-item">
              <span>Sources:</span> 
              <strong style={{ color: '#10b981' }}>{chunks.length} chunks</strong>
            </div>
            {!llmWasIncluded && (
              <div className="meta-item">
                <span style={{ color: '#c084fc', fontWeight: '600' }}>⚡ No Gemini calls</span>
              </div>
            )}
            {defenseEnabled && (
              <div className="meta-item">
                <span style={{ color: '#10b981', fontWeight: '600' }}>🛡️ Shielded</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Retrieved Chunks Drawer */}
      {chunks.length > 0 && (
        <details className="chunks-details" open={!llmWasIncluded}>
          <summary className="chunks-summary">
            <span>Show retrieved context sources ({chunks.length})</span>
            <span style={{ fontSize: '12px' }}>▼</span>
          </summary>
          <div style={{ background: 'rgba(0,0,0,0.2)' }}>
            {chunks.map((chunk, idx) => (
              <div key={idx} className="chunk-item">
                <div className="chunk-header">
                  Source Chunk #{idx + 1} {scores[idx] !== undefined && `(Score: ${scores[idx].toFixed(4)})`}
                </div>
                <div style={{ fontStyle: 'italic', color: '#9ca3af' }}>
                  "{chunk.length > 400 ? `${chunk.slice(0, 400)}...` : chunk}"
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </>
  )
}
