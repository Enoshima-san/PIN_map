import axios from 'axios'

// Единый экземпляр axios для запросов к backend.
// withCredentials нужен для отправки cookie серверной сессии вместе с запросами.
// SECURITY: при cookie-аутентификации сервер должен корректно проверять CSRF для изменяющих запросов.
const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Получить список объектов/маршрутов с фильтрами.
export async function fetchItems(params = {}) {
  const { data } = await api.get('/items/', { params })
  return data.results || data
}

// Получить одну запись по id. Сервер должен самостоятельно проверять доступ к записи.
export async function fetchItem(id) {
  const { data } = await api.get(`/items/${id}/`)
  return data
}

// Создать новую заявку. Нельзя доверять payload только потому, что он сформирован фронтендом.
export async function createItem(payload) {
  const { data } = await api.post('/items/', payload)
  return data
}

// Подтвердить объект/маршрут текущим пользователем.
export async function verifyItem(id) {
  const { data } = await api.post(`/items/${id}/verify/`)
  return data
}

// Действия модерации. SECURITY: права на эти endpoints обязательно проверяются на backend.
export async function approveItem(id) {
  const { data } = await api.post(`/items/${id}/approve/`)
  return data
}

export async function rejectItem(id) {
  const { data } = await api.post(`/items/${id}/reject/`)
  return data
}

// Добавление и удаление комментариев. Авторство и права удаления проверяются сервером.
export async function addComment(mapItemId, text) {
  const { data } = await api.post('/comments/', { map_item: mapItemId, text })
  return data
}

export async function deleteComment(id) {
  await api.delete(`/comments/${id}/`)
}

// Авторизация и регистрация. Пароль передаётся только в теле запроса и не сохраняется этим модулем.
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

// Проверяем текущую сессию. Если пользователь не вошёл, возвращаем null вместо ошибки в UI.
export async function getMe() {
  try {
    const { data } = await api.get('/auth/')
    return data
  } catch {
    return null
  }
}

// SECURITY: демонстрационный endpoint смены роли. В production его нужно удалить
// или разрешить только администратору, иначе возможна эскалация привилегий.
export async function toggleModerator() {
  const { data } = await api.post('/auth/toggle-moderator/')
  return data
}

export default api
