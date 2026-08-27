import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import Header from './components/Header.jsx'
import CalendarGrid from './components/CalendarGrid.jsx'
import Sidebar from './components/Sidebar.jsx'
import EventModal from './components/EventModal.jsx'
import SettingsModal from './components/SettingsModal.jsx'

export default function App() {
  const [today, setToday] = useState(null)
  const [view, setView] = useState(null) // { year, month } in BS
  const [calendar, setCalendar] = useState(null)
  const [events, setEvents] = useState([])
  const [upcoming, setUpcoming] = useState([])
  const [notif, setNotif] = useState(null)
  const [reminderPreview, setReminderPreview] = useState(null)
  const [lang, setLang] = useState('en')
  const [modal, setModal] = useState(null) // { mode, initial }
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [toast, setToast] = useState(null)
  const [error, setError] = useState(null)

  const flash = useCallback((msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3500)
  }, [])

  // Initial load: figure out "today" and open on the current BS month.
  useEffect(() => {
    api
      .today()
      .then((t) => {
        setToday(t)
        setView({ year: t.bs.year, month: t.bs.month })
      })
      .catch((e) => setError(e.message))
    api.notificationStatus().then(setNotif).catch(() => {})
  }, [])

  const refreshNotif = useCallback(
    () => api.notificationStatus().then(setNotif).catch(() => {}),
    [],
  )

  const loadCalendar = useCallback(() => {
    if (!view) return
    api
      .calendar(view.year, view.month)
      .then(setCalendar)
      .catch((e) => setError(e.message))
  }, [view])

  const loadEvents = useCallback(() => {
    api.listEvents().then(setEvents).catch((e) => setError(e.message))
    api.upcoming(45).then(setUpcoming).catch(() => {})
  }, [])

  useEffect(() => {
    loadCalendar()
  }, [loadCalendar])
  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const refresh = useCallback(() => {
    loadCalendar()
    loadEvents()
  }, [loadCalendar, loadEvents])

  const goTo = (target) => setView({ year: target.year, month: target.month })
  const goToday = () =>
    today && setView({ year: today.bs.year, month: today.bs.month })

  const openCreate = (day) =>
    setModal({
      mode: 'create',
      initial: { ad_date: day?.ad_date || today?.ad_date },
    })

  const openEdit = (id) => {
    const ev = events.find((e) => e.id === id)
    if (ev) setModal({ mode: 'edit', initial: ev })
  }

  const saveEvent = async (payload) => {
    if (modal.mode === 'edit') {
      await api.updateEvent(modal.initial.id, payload)
      flash('Event updated')
    } else {
      await api.createEvent(payload)
      flash('Event added')
    }
    setModal(null)
    refresh()
  }

  const deleteEvent = async (id) => {
    if (!window.confirm('Delete this event?')) return
    await api.deleteEvent(id)
    setModal(null)
    flash('Event deleted')
    refresh()
  }

  const previewReminders = async () => {
    try {
      const p = await api.previewReminders()
      setReminderPreview(p)
      flash(
        p.count === 0
          ? 'No reminders are due right now'
          : `${p.count} reminder${p.count > 1 ? 's' : ''} ready — see the sidebar`,
      )
    } catch (e) {
      flash(e.message)
    }
  }

  const content = useMemo(() => {
    if (error)
      return (
        <div className="fatal">
          <h2>Can’t reach the API</h2>
          <p>{error}</p>
          <p className="fatal__hint">
            Is the backend running? (default <code>:8200</code> with Docker)
          </p>
        </div>
      )
    return (
      <>
        <Header
          calendar={calendar}
          today={today}
          lang={lang}
          notif={notif}
          onPrev={() => calendar && goTo(calendar.prev)}
          onNext={() => calendar && goTo(calendar.next)}
          onToday={goToday}
          onToggleLang={() => setLang((l) => (l === 'en' ? 'np' : 'en'))}
          onAdd={() => openCreate(null)}
          onPreviewReminders={previewReminders}
          onOpenSettings={() => setSettingsOpen(true)}
        />
        <div className="layout">
          <main className="main">
            <CalendarGrid
              calendar={calendar}
              lang={lang}
              onSelectDay={openCreate}
              onEventClick={openEdit}
            />
          </main>
          <Sidebar
            upcoming={upcoming}
            events={events}
            onEdit={openEdit}
            notif={notif}
            reminderPreview={reminderPreview}
            todayIso={today?.ad_date}
          />
        </div>
      </>
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calendar, today, lang, notif, upcoming, events, reminderPreview, error])

  return (
    <div className="app">
      {content}
      {modal && (
        <EventModal
          mode={modal.mode}
          initial={modal.initial}
          onSave={saveEvent}
          onDelete={deleteEvent}
          onClose={() => setModal(null)}
          onConvert={api.convert}
        />
      )}
      {settingsOpen && (
        <SettingsModal
          status={notif}
          onClose={() => setSettingsOpen(false)}
          onSaved={refreshNotif}
          flash={flash}
        />
      )}
      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
