import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

export async function fetchItems(params = {}) {
  const { data } = await api.get('/items/', { params })
  return data.results || data
}

export async function fetchItem(id) {
  const { data } = await api.get(`/items/${id}/`)
  return data
}

export async function createItem(payload) {
  const { data } = await api.post('/items/', payload)
  return data
}

export async function verifyItem(id) {
  const { data } = await api.post(`/items/${id}/verify/`)
  return data
}

export async function approveItem(id) {
  const { data } = await api.post(`/items/${id}/approve/`)
  return data
}

export async function rejectItem(id) {
  const { data } = await api.post(`/items/${id}/reject/`)
  return data
}

export async function addComment(mapItemId, text) {
  const { data } = await api.post('/comments/', { map_item: mapItemId, text })
  return data
}

export async function deleteComment(id) {
  await api.delete(`/comments/${id}/`)
}

export async function login(email, password) {
  const { data } = await api.post('/auth/', { action: 'login', email, password })
  return data
}

export async function register(email, password) {
  const { data } = await api.post('/auth/', { action: 'register', email, password })
  return data
}

export async function logout() {
  await api.delete('/auth/')
}

export async function getMe() {
  try {
    const { data } = await api.get('/auth/')
    return data
  } catch {
    return null
  }
}

export async function toggleModerator() {
  const { data } = await api.post('/auth/toggle-moderator/')
  return data
}

export default api
