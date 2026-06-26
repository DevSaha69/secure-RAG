import { useState } from 'react'
import { uploadPDF, queryRAG } from './api/client'
import './App.css'

export default function App() {
  const [strategy, setStrategy] = useState('mmr')
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [chunks, setChunks] = useState([])
  const [scores, setScores] = useState([])
  const [timeMs, setTimeMs] = useState(0)
  const [loading, setLoading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploadStatus('Uploading and indexing...')
    try {
      const { data } = await uploadPDF(file)
      setUploadStatus(`✅ Successfully indexed ${data.chunks_stored} chunks from "${data.filename}"`)
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || 'Error uploading document. Please check server logs.';
      setUploadStatus(`❌ ${errorMsg}`)
    }
  }

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    setAnswer('')
    setChunks([])
    setScores([])
    try {
      const { data } = await queryRAG(query, strategy)
      setAnswer(data.answer)
      setChunks(data.chunks || [])
      setScores(data.scores || [])
      setTimeMs(data.time_ms || 0)
    } catch (err) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || 'Error fetching answer. Make sure backend is running and GEMINI_API_KEY is configured in backend/.env.';
      setAnswer(`❌ ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard-container">
      <h1 className="app-title">⚔ SECURE RAG</h1>
      <p className="app-subtitle">A Security-Focused Retrieval-Augmented Generation Platform</p>

      {/* Upload Zone */}
      <div className="section-card">
        <h2 className="section-title">Knowledge Base Ingestion</h2>
        <label className="upload-zone">
          <div className="upload-icon">📂</div>
          <div className="upload-label">
            Click to upload a PDF document and index it in ChromaDB
          </div>
          <input 
            type="file" 
            accept=".pdf" 
            className="upload-input" 
            onChange={handleUpload} 
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
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </div>

      {/* Generated Response */}
      {answer && (
        <div className="result-card">
          <div className="result-title">Response</div>
          <div className="result-text">{answer}</div>
          
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
          </div>
        </div>
      )}

      {/* Retrieved Chunks Drawer */}
      {chunks.length > 0 && (
        <details className="chunks-details">
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
    </div>
  )
}
