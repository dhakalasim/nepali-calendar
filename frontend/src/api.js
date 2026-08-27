const BASE = import.meta.env.VITE_API_BASE || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail
    try {
      const body = await res.json()
      detail = body.detail
    } catch {
      detail = null
    }
    throw new Error(
      typeof detail === 'string' ? detail : `Request failed (${res.status})`,
    )
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  today: () => request('/today'),
  convert: (params) => request(`/convert?${new URLSearchParams(params)}`),
  calendar: (year, month) => request(`/calendar?year=${year}&month=${month}`),
  listEvents: () => request('/events'),
  upcoming: (days = 45) => request(`/events/upcoming?days=${days}`),
  createEvent: (body) =>
    request('/events', { method: 'POST', body: JSON.stringify(body) }),
  updateEvent: (id, body) =>
    request(`/events/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteEvent: (id) => request(`/events/${id}`, { method: 'DELETE' }),
  sendEventReminderNow: (id, channels = 'all') =>
    request(`/events/${id}/send-reminder`, {
      method: 'POST',
      body: JSON.stringify({ channels }),
    }),
  notificationStatus: () => request('/notifications/status'),
  previewReminders: () => request('/notifications/preview'),
  runReminders: () => request('/notifications/run', { method: 'POST' }),
  getNotifSettings: () => request('/notifications/settings'),
  updateNotifSettings: (body) =>
    request('/notifications/settings', { method: 'PUT', body: JSON.stringify(body) }),
  sendTest: (channels) =>
    request('/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ channels: channels ?? null }),
    }),
}
