import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const uploadPDF = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const queryRAG = (query, strategy = 'mmr', top_k = 3) =>
  api.post('/query', { query, strategy, top_k })

export default api
