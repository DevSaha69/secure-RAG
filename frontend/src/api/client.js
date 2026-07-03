import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadPDF = (file, collection = 'gpt2_paper') => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/upload?collection=${encodeURIComponent(collection)}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const queryRAG = (query, strategy = 'mmr', top_k = 3, collection = 'gpt2_paper', include_llm = true, defense_enabled = false) =>
  api.post('/query', { query, strategy, top_k, collection, include_llm, defense_enabled })

export const runAttack = (payload) =>
  api.post('/attack', payload)

export const cleanupAttack = (attack_type, collection = 'gpt2_paper') =>
  api.post('/cleanup', { attack_type, collection })

export const getCollectionStats = (collection = 'gpt2_paper') =>
  api.get('/collection-stats', { params: { collection } })

export const getCollectionHealth = (collection = 'gpt2_paper') =>
  api.get('/health', { params: { collection } })

export const getAnomalyScan = (collection = 'gpt2_paper') =>
  api.get('/anomaly-scan', { params: { collection } })

export const getCollections = () =>
  api.get('/collections')


export const deleteCollection = (name) =>
  api.delete(`/collections/${encodeURIComponent(name)}`)

export default api
