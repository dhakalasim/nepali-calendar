import {
  BS_MONTHS_EN,
  CATEGORY_COLOR,
  RECURRENCE_OPTIONS,
  daysUntilLabel,
} from '../constants.js'

const RECUR_LABEL = Object.fromEntries(
  RECURRENCE_OPTIONS.map((o) => [o.value, o.label]),
)

function bsShort(bs) {
  return `${BS_MONTHS_EN[bs.month - 1]} ${bs.day}, ${bs.year}`
}

function adShort(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

// Recurring events first, then upcoming one-offs (soonest first),
// then past one-offs (most recent first).
function sortForManagement(events, todayIso) {
  const bucket = (ev) => {
    if (ev.recurrence !== 'none') return 0
    return ev.ad_date >= todayIso ? 1 : 2
  }
  return [...(events || [])].sort((a, b) => {
    const ba = bucket(a)
    const bb = bucket(b)
    if (ba !== bb) return ba - bb
    if (ba === 2) return a.ad_date < b.ad_date ? 1 : -1
    return a.ad_date < b.ad_date ? -1 : 1
  })
}

export default function Sidebar({
  upcoming,
  events,
  onEdit,
  notif,
  reminderPreview,
  todayIso,
}) {
  const sortedEvents = sortForManagement(events, todayIso || '0000-00-00')
  return (
    <aside className="sidebar">
      {reminderPreview && (
        <section className="panel panel--preview">
          <h2 className="panel__title">Reminder preview</h2>
          {reminderPreview.count === 0 ? (
            <p className="panel__empty">
              Nothing is inside its reminder window right now.
            </p>
          ) : (
            <>
              <p className="panel__note">
                {notif?.email_enabled
                  ? `Would email ${notif.recipients.join(', ')}:`
                  : 'SMTP off — this would print to the backend console:'}
              </p>
              <ul className="mini-list">
                {reminderPreview.items.map((it) => (
                  <li key={it.event_id}>
                    <strong>{it.title}</strong> — {daysUntilLabel(it.days_until)}
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      <section className="panel">
        <h2 className="panel__title">Upcoming</h2>
        {(!upcoming || upcoming.length === 0) && (
          <p className="panel__empty">No dates in the next 45 days.</p>
        )}
        <ul className="event-list">
          {upcoming?.map((o) => (
            <li
              key={`${o.event.id}-${o.occurrence_ad}`}
              className="event-row"
              onClick={() => onEdit(o.event.id)}
            >
              <span
                className="event-row__dot"
                style={{ background: CATEGORY_COLOR[o.event.category] || '#64748b' }}
              />
              <div className="event-row__body">
                <div className="event-row__title">{o.event.title}</div>
                <div className="event-row__meta">
                  {bsShort(o.occurrence_bs)} · {adShort(o.occurrence_ad)}
                </div>
              </div>
              <span className="event-row__when">
                {daysUntilLabel(o.days_until)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2 className="panel__title">All events ({events?.length || 0})</h2>
        <ul className="event-list event-list--scroll">
          {sortedEvents.map((ev) => (
            <li
              key={ev.id}
              className="event-row"
              onClick={() => onEdit(ev.id)}
            >
              <span
                className="event-row__dot"
                style={{ background: CATEGORY_COLOR[ev.category] || '#64748b' }}
              />
              <div className="event-row__body">
                <div className="event-row__title">
                  {ev.title}
                  {ev.source === 'seed' && <span className="tag">holiday</span>}
                </div>
                <div className="event-row__meta">
                  {bsShort({ year: ev.bs_year, month: ev.bs_month, day: ev.bs_day })}
                  {ev.recurrence !== 'none' && (
                    <> · ↻ {RECUR_LABEL[ev.recurrence]}</>
                  )}
                  {!ev.notify_enabled && <> · muted</>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </aside>
  )
}
