import React, { useState, useEffect, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import * as api from './api'

const CENTER = [53.7585, 87.1350]
const ZOOM = 14

function privacyClass(p) {
  if (p === 'тихий') return 'badge-privacy-quiet'
  if (p === 'высокий') return 'badge-privacy-high'
  return 'badge-privacy-med'
}

function statusBadge(status) {
  if (status === 'approved') return <span className="badge" style={{ background: 'rgba(46,204,113,0.15)', color: '#2ecc71' }}>Одобрено</span>
  if (status === 'pending') return <span className="badge" style={{ background: 'rgba(243,156,18,0.15)', color: '#f39c12' }}>На модерации</span>
  return <span className="badge" style={{ background: 'rgba(231,76,60,0.15)', color: '#e74c3c' }}>Отклонено</span>
}

function MapClickHandler({ createType, onObjectCoord, onRoutePoint }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng
      if (createType === 'object') onObjectCoord([lat, lng])
      else onRoutePoint([lat, lng])
    },
  })
  return null
}

function FlyTo({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.flyTo(center, zoom || 15)
  }, [center, zoom, map])
  return null
}

export default function App() {
  const [tab, setTab] = useState('catalog')
  const [catalogMode, setCatalogMode] = useState('objects')
  const [items, setItems] = useState([])
  const [myItems, setMyItems] = useState([])
  const [modItems, setModItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [user, setUser] = useState(null)
  const [online, setOnline] = useState(navigator.onLine)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState({ privacy: '', category: '', objActivity: '', routeActivity: '' })
  const [myFilters, setMyFilters] = useState({ status: '', type: '' })
  const [modStatus, setModStatus] = useState('pending')
  const [createType, setCreateType] = useState('object')
  const [objectCoord, setObjectCoord] = useState(null)
  const [routePoints, setRoutePoints] = useState([])
  const [flyTarget, setFlyTarget] = useState(null)
  const [authMode, setAuthMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [highlightRouteId, setHighlightRouteId] = useState(null)

  // forms
  const [createForm, setCreateForm] = useState({
    title: '', desc: '', category: 'Культурное наследие', privacy: 'тихий',
    objActivity: 'Прогулка', routeActivity: 'Пеший маршрут', duration: 45,
  })
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [regForm, setRegForm] = useState({ email: '', password: '', confirm: '' })
  const [commentText, setCommentText] = useState('')

  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off) }
  }, [])

  useEffect(() => {
    api.getMe().then(u => setUser(u)).catch(() => {})
  }, [])

  const loadCatalog = useCallback(async () => {
    try {
      const params = { status: 'approved', item_type: catalogMode === 'objects' ? 'object' : 'route' }
      if (search) params.search = search
      if (catalogMode === 'objects') {
        if (filters.privacy) params.privacy = filters.privacy
        if (filters.category) params.category = filters.category
        if (filters.objActivity) params.activity_type = filters.objActivity
      } else if (filters.routeActivity) {
        params.activity_type = filters.routeActivity
      }
      const data = await api.fetchItems(params)
      setItems(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error(e)
    }
  }, [catalogMode, search, filters])

  useEffect(() => { loadCatalog() }, [loadCatalog])

  const loadMyItems = useCallback(async () => {
    if (!user) return
    try {
      const params = { mine: 1 }
      if (myFilters.status) params.status = myFilters.status
      if (myFilters.type) params.item_type = myFilters.type
      const data = await api.fetchItems(params)
      setMyItems(Array.isArray(data) ? data : [])
    } catch (e) { console.error(e) }
  }, [user, myFilters])

  useEffect(() => { if (tab === 'my-items') loadMyItems() }, [tab, loadMyItems])

  const loadModeration = useCallback(async () => {
    try {
      const data = await api.fetchItems({ status: modStatus })
      setModItems(Array.isArray(data) ? data : [])
    } catch (e) { console.error(e) }
  }, [modStatus])

  useEffect(() => { if (tab === 'moderation') loadModeration() }, [tab, loadModeration])

  const openDetail = async (id) => {
    try {
      const item = await api.fetchItem(id)
      setSelected(item)
      if (item.lat && item.lng) setFlyTarget([item.lat, item.lng])
      setTab('catalog')
    } catch (e) { console.error(e) }
  }

  const closeDetail = () => {
    setSelected(null)
    setFlyTarget(null)
  }

  const handleVerify = async () => {
    if (!user) { alert('Войдите в аккаунт'); setTab('account'); return }
    try {
      const res = await api.verifyItem(selected.id)
      setSelected(s => ({ ...s, verifications: res.verifications }))
      setUser(u => u ? { ...u, verified_count: (u.verified_count || 0) + 1 } : u)
      alert('Спасибо! Ваше подтверждение учтено.')
    } catch (e) {
      alert(e.response?.data?.detail || 'Ошибка')
    }
  }

  const handleAddComment = async (e) => {
    e.preventDefault()
    if (!commentText.trim() || !selected) return
    try {
      await api.addComment(selected.id, commentText.trim())
      const item = await api.fetchItem(selected.id)
      setSelected(item)
      setCommentText('')
    } catch (e) { alert('Ошибка добавления комментария') }
  }

  const handleDeleteComment = async (cid) => {
    try {
      await api.deleteComment(cid)
      setSelected(s => ({ ...s, comments: s.comments.filter(c => c.id !== cid) }))
    } catch (e) { alert('Не удалось удалить') }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!user) return
    const payload = {
      item_type: createType,
      title: createForm.title,
      description: createForm.desc,
    }
    if (createType === 'object') {
      if (!objectCoord) { alert('Кликните по карте для выбора координаты'); return }
      payload.lat = objectCoord[0]
      payload.lng = objectCoord[1]
      payload.category = createForm.category
      payload.privacy = createForm.privacy
      payload.activity_type = createForm.objActivity
    } else {
      if (routePoints.length < 2) { alert('Нужно минимум 2 точки маршрута'); return }
      payload.track_points = routePoints
      payload.activity_type = createForm.routeActivity
      payload.duration_minutes = parseInt(createForm.duration) || 30
      payload.category = 'Маршруты'
    }
    setLoading(true)
    try {
      await api.createItem(payload)
      alert('Заявка отправлена на модерацию!')
      setCreateForm({ title: '', desc: '', category: 'Культурное наследие', privacy: 'тихий', objActivity: 'Прогулка', routeActivity: 'Пеший маршрут', duration: 45 })
      setObjectCoord(null)
      setRoutePoints([])
      setTab('my-items')
      loadMyItems()
    } catch (err) {
      alert(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Ошибка')
    } finally { setLoading(false) }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const u = await api.login(loginForm.email, loginForm.password)
      setUser(u)
      setTab('catalog')
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка входа') }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    if (regForm.password !== regForm.confirm) { alert('Пароли не совпадают'); return }
    try {
      const u = await api.register(regForm.email, regForm.password)
      setUser(u)
      setTab('catalog')
    } catch (err) { alert(err.response?.data?.detail || 'Ошибка регистрации') }
  }

  const handleLogout = async () => {
    await api.logout()
    setUser(null)
    setTab('account')
  }

  const handleToggleRole = async () => {
    if (!user) { alert('Сначала войдите'); setTab('account'); return }
    try {
      const u = await api.toggleModerator()
      setUser(u)
    } catch (e) { alert('Ошибка') }
  }

  const onObjectCoord = (coord) => {
    setObjectCoord(coord)
    setTab('create')
  }
  const onRoutePoint = (pt) => {
    setRoutePoints(prev => [...prev, pt])
    setTab('create')
  }

  const visibleItems = items
  const routes = visibleItems.filter(i => i.item_type === 'route' && i.track_coordinates)

  return (
    <>
      <div id="sidebar">
        <div className="header-title">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <h2>PiN</h2>
              <div className="network-dot" style={{ backgroundColor: online ? 'var(--status-approved)' : 'var(--status-rejected)' }}
                title={online ? 'Онлайн' : 'Нет подключения'} />
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Социальная карта прогулок</p>
          </div>
          <div className={`role-badge ${user ? 'active' : ''}`} onClick={handleToggleRole}>
            {user ? (user.email || user.username) : 'Гость'}
          </div>
        </div>

        <div className="tabs-nav">
          <button className={`tab-btn ${tab === 'catalog' ? 'active' : ''}`} onClick={() => { setTab('catalog'); closeDetail() }}>Каталог</button>
          <button className={`tab-btn ${tab === 'create' ? 'active' : ''}`} onClick={() => setTab('create')}>Создать</button>
          {user && <button className={`tab-btn ${tab === 'my-items' ? 'active' : ''}`} onClick={() => setTab('my-items')}>Мои заявки</button>}
          {user?.is_moderator && <button className={`tab-btn ${tab === 'moderation' ? 'active' : ''}`} onClick={() => setTab('moderation')}>Модерация</button>}
          <button className={`tab-btn ${tab === 'account' ? 'active' : ''}`} onClick={() => setTab('account')}>Аккаунт</button>
        </div>

        {/* CATALOG */}
        <div className={`tab-content ${tab === 'catalog' ? 'active' : ''}`}>
          {!selected ? (
            <div>
              <div className="mode-switch">
                <button className={`mode-switch-btn ${catalogMode === 'objects' ? 'active' : ''}`} onClick={() => setCatalogMode('objects')}>Объекты</button>
                <button className={`mode-switch-btn ${catalogMode === 'routes' ? 'active' : ''}`} onClick={() => setCatalogMode('routes')}>Маршруты</button>
              </div>
              <div className="input-group">
                <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Поиск на карте..." />
              </div>
              {catalogMode === 'objects' ? (
                <>
                  <div className="input-group">
                    <label>Уровень уединённости</label>
                    <select value={filters.privacy} onChange={e => setFilters(f => ({ ...f, privacy: e.target.value }))}>
                      <option value="">Все уровни</option>
                      <option value="тихий">Тихий</option>
                      <option value="средний">Средний</option>
                      <option value="высокий">Высокий</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Категория объекта</label>
                    <select value={filters.category} onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}>
                      <option value="">Все категории</option>
                      <option value="Культурное наследие">Культурное наследие</option>
                      <option value="Уличное искусство">Уличное искусство</option>
                      <option value="Природный объект">Природный объект</option>
                      <option value="Парки и отдых">Парки и отдых</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Тип активности</label>
                    <select value={filters.objActivity} onChange={e => setFilters(f => ({ ...f, objActivity: e.target.value }))}>
                      <option value="">Все активности</option>
                      <option value="Прогулка">Прогулка</option>
                      <option value="Фотосессия">Фотосессия</option>
                      <option value="Велосипед">Велосипед</option>
                      <option value="Экскурсия">Экскурсия</option>
                    </select>
                  </div>
                </>
              ) : (
                <div className="input-group">
                  <label>Тип активности (маршрут)</label>
                  <select value={filters.routeActivity} onChange={e => setFilters(f => ({ ...f, routeActivity: e.target.value }))}>
                    <option value="">Все активности</option>
                    <option value="Пеший маршрут">Пеший маршрут</option>
                    <option value="Веломаршрут">Веломаршрут</option>
                    <option value="Бег">Бег</option>
                  </select>
                </div>
              )}
              <div>
                {visibleItems.length === 0 ? <p className="muted">Записи не найдены</p> : visibleItems.map(item => (
                  <div key={item.id} className="item-card"
                    onClick={() => openDetail(item.id)}
                    onMouseEnter={() => item.item_type === 'route' && setHighlightRouteId(item.id)}
                    onMouseLeave={() => setHighlightRouteId(null)}>
                    <h4>{item.title}</h4>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.address || 'Маршрут'}</p>
                    <div>
                      <span className="badge badge-type">{item.activity_type}</span>
                      {item.item_type === 'object' && item.privacy && (
                        <span className={`badge ${privacyClass(item.privacy)}`}>Уединённость: {item.privacy}</span>
                      )}
                      {item.duration_minutes && <span className="badge badge-type">~{item.duration_minutes} мин</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="detail-panel active">
              <button className="back-btn" onClick={closeDetail}>← Назад к каталогу</button>
              <h3 style={{ fontSize: 18, color: '#fff' }}>{selected.title}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{selected.address}</p>
              <div>
                <span className="badge badge-type">{selected.activity_type}</span>
                {selected.category && <span className="badge badge-type">{selected.category}</span>}
                {selected.privacy && <span className={`badge ${privacyClass(selected.privacy)}`}>Уединённость: {selected.privacy}</span>}
                {selected.duration_minutes && <span className="badge badge-type">~{selected.duration_minutes} мин</span>}
              </div>
              {selected.item_type === 'object' && (
                <div>
                  <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Фотоматериал</label>
                  <div className="media-gallery">
                    <img src={selected.image_display || selected.image_url || ''} alt="Фото" />
                  </div>
                </div>
              )}
              <p style={{ fontSize: 13, lineHeight: 1.5, color: '#ddd' }}>{selected.description}</p>
              <button className="btn-submit" style={{ background: 'var(--bg-card)', border: '1px solid var(--accent-color)', color: 'var(--status-approved)' }}
                onClick={handleVerify}>
                ✓ Подтвердить существование ({selected.verifications})
              </button>
              <div>
                <label style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Навигация</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={{ flex: 1, padding: 9, background: '#fc3f1d', border: 'none', color: '#fff', borderRadius: 6, fontWeight: 'bold', cursor: 'pointer', fontSize: 12 }}
                    onClick={() => window.open(`https://yandex.ru/maps/?pt=${selected.lng},${selected.lat}&z=16&l=map`, '_blank')}>Яндекс Карты</button>
                  <button style={{ flex: 1, padding: 9, background: '#60a700', border: 'none', color: '#fff', borderRadius: 6, fontWeight: 'bold', cursor: 'pointer', fontSize: 12 }}
                    onClick={() => window.open(`https://2gis.ru/geo/${selected.lng},${selected.lat}`, '_blank')}>2ГИС</button>
                </div>
              </div>
              <hr style={{ borderColor: 'var(--border-color)', margin: '8px 0' }} />
              <h4 style={{ fontSize: 14 }}>Отзывы и комментарии</h4>
              <div>
                {(!selected.comments || selected.comments.length === 0)
                  ? <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Пока нет отзывов.</p>
                  : selected.comments.map(c => (
                    <div key={c.id} className="comment-item">
                      <div style={{ fontWeight: 'bold', fontSize: 11, color: 'var(--accent-color)' }}>{c.author_email || c.author}</div>
                      <div style={{ marginTop: 2 }}>{c.text}</div>
                      {user && (user.email === c.author_email || user.id === c.author) && (
                        <button className="btn-delete-comment" onClick={() => handleDeleteComment(c.id)}>Удалить</button>
                      )}
                    </div>
                  ))}
              </div>
              {user && (
                <form onSubmit={handleAddComment} style={{ marginTop: 8 }}>
                  <input type="text" value={commentText} onChange={e => setCommentText(e.target.value)} placeholder="Оставить отзыв..." required style={{ marginBottom: 8 }} />
                  <button type="submit" className="btn-submit" style={{ padding: 9, fontSize: 13 }}>Отправить</button>
                </form>
              )}
            </div>
          )}
        </div>

        {/* CREATE */}
        <div className={`tab-content ${tab === 'create' ? 'active' : ''}`}>
          {!user ? (
            <div style={{ textAlign: 'center', padding: '30px 10px' }}>
              <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 16 }}>Чтобы создавать объекты или маршруты, войдите в аккаунт.</p>
              <button className="btn-submit" onClick={() => setTab('account')}>Перейти к аккаунту</button>
            </div>
          ) : (
            <form onSubmit={handleCreate}>
              <h3 style={{ marginBottom: 10, fontSize: 16 }}>Новая запись на модерацию</h3>
              <div className="mode-switch">
                <button type="button" className={`mode-switch-btn ${createType === 'object' ? 'active' : ''}`} onClick={() => { setCreateType('object'); setRoutePoints([]) }}>Объект</button>
                <button type="button" className={`mode-switch-btn ${createType === 'route' ? 'active' : ''}`} onClick={() => { setCreateType('route'); setObjectCoord(null) }}>Маршрут</button>
              </div>
              <div className="input-group">
                <label>Название</label>
                <input type="text" value={createForm.title} onChange={e => setCreateForm(f => ({ ...f, title: e.target.value }))} required placeholder="Введите название..." />
              </div>
              {createType === 'object' ? (
                <>
                  <div className="input-group">
                    <label>Категория объекта</label>
                    <select value={createForm.category} onChange={e => setCreateForm(f => ({ ...f, category: e.target.value }))}>
                      <option value="Культурное наследие">Культурное наследие</option>
                      <option value="Уличное искусство">Уличное искусство</option>
                      <option value="Природный объект">Природный объект</option>
                      <option value="Парки и отдых">Парки и отдых</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Уровень уединённости</label>
                    <select value={createForm.privacy} onChange={e => setCreateForm(f => ({ ...f, privacy: e.target.value }))}>
                      <option value="тихий">Тихий</option>
                      <option value="средний">Средний</option>
                      <option value="высокий">Высокий</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Тип активности</label>
                    <select value={createForm.objActivity} onChange={e => setCreateForm(f => ({ ...f, objActivity: e.target.value }))}>
                      <option value="Прогулка">Прогулка</option>
                      <option value="Фотосессия">Фотосессия</option>
                      <option value="Велосипед">Велосипед</option>
                      <option value="Экскурсия">Экскурсия</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Координата объекта (кликните по карте)</label>
                    <input type="text" readOnly value={objectCoord ? `${objectCoord[0].toFixed(5)}, ${objectCoord[1].toFixed(5)}` : ''} placeholder="Выберите точку на карте..." style={{ cursor: 'pointer', background: '#1a1a20' }} />
                  </div>
                </>
              ) : (
                <>
                  <div className="input-group">
                    <label>Тип активности (для маршрута)</label>
                    <select value={createForm.routeActivity} onChange={e => setCreateForm(f => ({ ...f, routeActivity: e.target.value }))}>
                      <option value="Пеший маршрут">Пеший маршрут</option>
                      <option value="Веломаршрут">Веломаршрут</option>
                      <option value="Бег">Бег</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label>Примерное время прохождения (мин)</label>
                    <input type="number" value={createForm.duration} onChange={e => setCreateForm(f => ({ ...f, duration: e.target.value }))} placeholder="45" />
                  </div>
                  <div className="input-group">
                    <label>Точки маршрута (кликайте по карте)</label>
                    <div style={{ fontSize: 12, background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 8, marginBottom: 6, maxHeight: 90, overflowY: 'auto', color: 'var(--text-muted)' }}>
                      {routePoints.length === 0 ? 'Точки не добавлены (минимум 2)' : (
                        <ul style={{ paddingLeft: 16, margin: 0 }}>
                          {routePoints.map((pt, i) => <li key={i}>Точка {i + 1}: {pt[0].toFixed(4)}, {pt[1].toFixed(4)}</li>)}
                        </ul>
                      )}
                    </div>
                    <button type="button" onClick={() => setRoutePoints([])}
                      style={{ padding: '6px 10px', background: 'rgba(231,76,60,0.15)', border: '1px solid var(--status-rejected)', color: 'var(--status-rejected)', borderRadius: 6, fontSize: 11, cursor: 'pointer', fontWeight: 'bold' }}>
                      Очистить точки маршрута
                    </button>
                  </div>
                </>
              )}
              <div className="input-group">
                <label>Описание</label>
                <textarea rows={3} value={createForm.desc} onChange={e => setCreateForm(f => ({ ...f, desc: e.target.value }))} placeholder="Опишите особенности места или путь маршрута..." />
              </div>
              <button type="submit" className="btn-submit" disabled={loading}>{loading ? 'Отправка...' : 'Отправить на модерацию'}</button>
            </form>
          )}
        </div>

        {/* MY ITEMS */}
        <div className={`tab-content ${tab === 'my-items' ? 'active' : ''}`}>
          <h3 style={{ marginBottom: 10, fontSize: 16 }}>Мои созданные объекты и маршруты</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>Здесь вы можете отслеживать статус модерации каждой вашей заявки.</p>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="num">{user?.added_count ?? myItems.length}</div>
              <div className="label">Создано заявок</div>
            </div>
            <div className="stat-card">
              <div className="num" style={{ color: 'var(--status-approved)' }}>{user?.verified_count ?? 0}</div>
              <div className="label">Подтверждено</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <div className="input-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Статус заявки</label>
              <select value={myFilters.status} onChange={e => setMyFilters(f => ({ ...f, status: e.target.value }))}>
                <option value="">Все статусы</option>
                <option value="pending">На модерации</option>
                <option value="approved">Одобрено</option>
                <option value="rejected">Отклонено</option>
              </select>
            </div>
            <div className="input-group" style={{ flex: 1, marginBottom: 0 }}>
              <label>Тип заявки</label>
              <select value={myFilters.type} onChange={e => setMyFilters(f => ({ ...f, type: e.target.value }))}>
                <option value="">Все типы</option>
                <option value="object">Объекты</option>
                <option value="route">Маршруты</option>
              </select>
            </div>
          </div>
          {myItems.length === 0 ? <p className="muted">Заявки не найдены</p> : myItems.map(item => (
            <div key={item.id} className="item-card" onClick={() => item.status === 'approved' ? openDetail(item.id) : setFlyTarget([item.lat, item.lng])}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4>{item.title}</h4>
                {statusBadge(item.status)}
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Тип: {item.item_type === 'object' ? 'Объект' : 'Маршрут'} • {item.activity_type}
              </p>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Подтверждений: {item.verifications}</p>
            </div>
          ))}
        </div>

        {/* MODERATION */}
        <div className={`tab-content ${tab === 'moderation' ? 'active' : ''}`}>
          <h3 style={{ marginBottom: 10, fontSize: 16 }}>Заявки на модерацию</h3>
          <div className="input-group">
            <label>Фильтр по статусу</label>
            <select value={modStatus} onChange={e => setModStatus(e.target.value)}>
              <option value="pending">На модерации</option>
              <option value="approved">Одобрено</option>
              <option value="rejected">Отклонено</option>
            </select>
          </div>
          {modItems.length === 0 ? <p className="muted">Заявок нет</p> : modItems.map(item => (
            <div key={item.id} className="item-card" style={{ cursor: 'default' }}>
              <h4>{item.title}</h4>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>Автор: {item.author_email || '—'}</p>
              <p style={{ fontSize: 12, marginTop: 4 }}>{item.description || 'Без описания'}</p>
              <span className="badge badge-type">{item.activity_type}</span>
              {modStatus === 'pending' && (
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <button style={{ flex: 1, padding: 6, background: 'var(--status-approved)', border: 'none', color: '#fff', borderRadius: 4, fontWeight: 'bold', cursor: 'pointer' }}
                    onClick={async () => { await api.approveItem(item.id); loadModeration(); loadCatalog() }}>Одобрить</button>
                  <button style={{ flex: 1, padding: 6, background: 'var(--status-rejected)', border: 'none', color: '#fff', borderRadius: 4, fontWeight: 'bold', cursor: 'pointer' }}
                    onClick={async () => { await api.rejectItem(item.id); loadModeration() }}>Отклонить</button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* ACCOUNT */}
        <div className={`tab-content ${tab === 'account' ? 'active' : ''}`}>
          {!user ? (
            <>
              <div className="mode-switch" style={{ marginBottom: 16 }}>
                <button type="button" className={`mode-switch-btn ${authMode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode('login')}>Вход</button>
                <button type="button" className={`mode-switch-btn ${authMode === 'register' ? 'active' : ''}`} onClick={() => setAuthMode('register')}>Регистрация</button>
              </div>
              {authMode === 'login' ? (
                <form onSubmit={handleLogin}>
                  <div className="input-group"><label>Email</label>
                    <input type="email" value={loginForm.email} onChange={e => setLoginForm(f => ({ ...f, email: e.target.value }))} required placeholder="example@mail.ru" /></div>
                  <div className="input-group"><label>Пароль</label>
                    <input type="password" value={loginForm.password} onChange={e => setLoginForm(f => ({ ...f, password: e.target.value }))} required placeholder="••••••••" /></div>
                  <button type="submit" className="btn-submit">Войти</button>
                </form>
              ) : (
                <form onSubmit={handleRegister}>
                  <div className="input-group"><label>Email</label>
                    <input type="email" value={regForm.email} onChange={e => setRegForm(f => ({ ...f, email: e.target.value }))} required placeholder="example@mail.ru" /></div>
                  <div className="input-group"><label>Пароль</label>
                    <input type="password" value={regForm.password} onChange={e => setRegForm(f => ({ ...f, password: e.target.value }))} required placeholder="••••••••" /></div>
                  <div className="input-group"><label>Подтвердите пароль</label>
                    <input type="password" value={regForm.confirm} onChange={e => setRegForm(f => ({ ...f, confirm: e.target.value }))} required placeholder="••••••••" /></div>
                  <button type="submit" className="btn-submit">Зарегистрироваться</button>
                </form>
              )}
            </>
          ) : (
            <div>
              <div style={{ textAlign: 'center', padding: '10px 0 16px' }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--accent-color)', color: '#fff', fontSize: 26, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px', fontWeight: 'bold' }}>
                  {(user.email || user.username || '@')[0].toUpperCase()}
                </div>
                <p style={{ fontSize: 13, color: '#fff', fontWeight: 'bold', marginBottom: 12, wordBreak: 'break-all' }}>{user.email || user.username}</p>
              </div>
              <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: 8, padding: 12, marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 'bold', marginBottom: 8, color: 'var(--text-muted)' }}>Информация</div>
                <div style={{ fontSize: 13, display: 'flex', justifyContent: 'space-between' }}>
                  <span>Статус аккаунта:</span>
                  <span style={{ color: 'var(--status-approved)', fontWeight: 600 }}>Активен</span>
                </div>
                <div style={{ fontSize: 13, display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                  <span>Модератор:</span>
                  <span style={{ color: user.is_moderator ? 'var(--status-approved)' : 'var(--text-muted)', fontWeight: 600 }}>
                    {user.is_moderator ? 'Да' : 'Нет'}
                  </span>
                </div>
              </div>
              <button onClick={handleLogout} style={{ width: '100%', padding: 10, background: 'rgba(231,76,60,0.15)', border: '1px solid var(--status-rejected)', color: 'var(--status-rejected)', borderRadius: 8, cursor: 'pointer', fontWeight: 'bold', fontSize: 13 }}>
                Выйти из аккаунта
              </button>
            </div>
          )}
        </div>
      </div>

      <div id="map-container">
        <MapContainer center={CENTER} zoom={ZOOM} style={{ width: '100%', height: '100%' }} attributionControl={false}>
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={16}
          />
          <MapClickHandler createType={createType} onObjectCoord={onObjectCoord} onRoutePoint={onRoutePoint} />
          {flyTarget && <FlyTo center={flyTarget} zoom={15} />}

          {visibleItems.map(item => item.lat && item.lng && (
            <CircleMarker key={item.id} center={[item.lat, item.lng]}
              radius={8}
              pathOptions={{
                fillColor: item.item_type === 'route' ? '#64b5f6' : '#3e8e60',
                color: '#fff', weight: 2, fillOpacity: 0.95,
              }}
              eventHandlers={{ click: () => openDetail(item.id) }}>
            </CircleMarker>
          ))}

          {routes.map(item => (
            <Polyline key={`route-${item.id}`}
              positions={item.track_coordinates}
              pathOptions={{
                color: highlightRouteId === item.id || selected?.id === item.id ? '#ffeb3b' : '#64b5f6',
                weight: highlightRouteId === item.id || selected?.id === item.id ? 7 : 5,
                opacity: 0.9,
              }}
            />
          ))}

          {routePoints.length > 0 && (
            <Polyline positions={routePoints} pathOptions={{ color: '#ffeb3b', weight: 4, dashArray: '5, 5' }} />
          )}
          {objectCoord && (
            <CircleMarker center={objectCoord} radius={10} pathOptions={{ fillColor: '#ffeb3b', color: '#fff', weight: 2, fillOpacity: 1 }} />
          )}
        </MapContainer>
      </div>
    </>
  )
}
