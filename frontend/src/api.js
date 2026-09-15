const API_BASE = import.meta.env.VITE_API_BASE || ''

function detailMessage(data, fallback) {
  const detail = data?.detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('；')
  }
  return detail || fallback
}

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!res.ok) {
    const err = new Error(detailMessage(data, '请求失败'))
    err.status = res.status
    throw err
  }
  return data
}

async function uploadForm(path, fileList, token) {
  const files = [...fileList].map((f) => (f && typeof f === 'object' && 'size' in f ? f : null)).filter(Boolean)
  const empty = files.filter((f) => !f.size)
  if (empty.length) {
    throw new Error(
      `「${empty.map((f) => f.name).join('、')}」是空文件（0 字节）。请先保存文件内容后再上传。`,
    )
  }
  const form = new FormData()
  files.forEach((f) => form.append('files', f, f.name))
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: form })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(detailMessage(data, '上传失败'))
  return data
}

export function fileUrl(path) {
  if (!path) return ''
  if (/^https?:/i.test(path)) return path
  return `${API_BASE}${path}`
}

export const api = {
  health: () => request('/api/health'),
  sendCode: (email, purpose = 'register') =>
    request('/api/auth/send-code', { method: 'POST', body: { email, purpose } }),
  register: (payload) => request('/api/auth/register', { method: 'POST', body: payload }),
  login: (payload) => request('/api/auth/login', { method: 'POST', body: payload }),
  me: (token) => request('/api/auth/me', { token }),
  updateProfile: (payload, token) =>
    request('/api/auth/profile', { method: 'PATCH', body: payload, token }),
  sendPasswordCode: (token) =>
    request('/api/auth/password/send-code', { method: 'POST', token }),
  changePassword: (payload, token) =>
    request('/api/auth/password/change', { method: 'POST', body: payload, token }),
  resetPassword: (payload) =>
    request('/api/auth/password/reset', { method: 'POST', body: payload }),
  categories: () => request('/api/categories'),
  posts: (params = {}) => {
    const q = new URLSearchParams()
    if (params.category) q.set('category', params.category)
    if (params.skip != null) q.set('skip', params.skip)
    if (params.limit != null) q.set('limit', params.limit)
    const qs = q.toString()
    return request(`/api/posts${qs ? `?${qs}` : ''}`)
  },
  post: (id) => request(`/api/posts/${id}`),
  createPost: (payload, token) => request('/api/posts', { method: 'POST', body: payload, token }),
  deletePost: (id, token) => request(`/api/posts/${id}`, { method: 'DELETE', token }),
  comments: (postId) => request(`/api/posts/${postId}/comments`),
  createComment: (postId, payload, token) =>
    request(`/api/posts/${postId}/comments`, { method: 'POST', body: payload, token }),
  deleteComment: (postId, commentId, token) =>
    request(`/api/posts/${postId}/comments/${commentId}`, { method: 'DELETE', token }),
  upload: (kind, id, files, token) => uploadForm(`/api/${kind}/${id}/files`, files, token),
  daily: () => request('/api/daily'),
  dailyHistory: (limit = 60) => request(`/api/daily/history?limit=${limit}`),
  moments: () => request('/api/moments'),
  createMoment: (payload, token) => request('/api/moments', { method: 'POST', body: payload, token }),
  deleteMoment: (id, token) => request(`/api/moments/${id}`, { method: 'DELETE', token }),
  momentComments: (id) => request(`/api/moments/${id}/comments`),
  createMomentComment: (id, payload, token) =>
    request(`/api/moments/${id}/comments`, { method: 'POST', body: payload, token }),
  deleteMomentComment: (momentId, commentId, token) =>
    request(`/api/moments/${momentId}/comments/${commentId}`, { method: 'DELETE', token }),
  books: () => request('/api/books'),
  book: (id) => request(`/api/books/${id}`),
  createBook: (payload, token) => request('/api/books', { method: 'POST', body: payload, token }),
  deleteBook: (id, token) => request(`/api/books/${id}`, { method: 'DELETE', token }),
  bookComments: (id) => request(`/api/books/${id}/comments`),
  createBookComment: (id, payload, token) =>
    request(`/api/books/${id}/comments`, { method: 'POST', body: payload, token }),
  deleteBookComment: (bookId, commentId, token) =>
    request(`/api/books/${bookId}/comments/${commentId}`, { method: 'DELETE', token }),
  unreadCount: (token) => request('/api/notifications/unread-count', { token }),
  notifications: (token) => request('/api/notifications', { token }),
  readAllNotifications: (token) =>
    request('/api/notifications/read-all', { method: 'POST', token }),
  readNotification: (id, token) =>
    request(`/api/notifications/${id}/read`, { method: 'POST', token }),
  adminUsers: (token, q = '') =>
    request(`/api/admin/users${q ? `?q=${encodeURIComponent(q)}` : ''}`, { token }),
  adminUpdateUser: (id, payload, token) =>
    request(`/api/admin/users/${id}`, { method: 'PATCH', body: payload, token }),
  adminKickUser: (id, token) =>
    request(`/api/admin/users/${id}/kick`, { method: 'POST', token }),
  adminDeleteUser: (id, token) =>
    request(`/api/admin/users/${id}`, { method: 'DELETE', token }),
}
