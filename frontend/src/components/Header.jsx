import { BS_MONTHS_EN, BS_MONTHS_NP, toNepaliDigits } from '../constants.js'

function todayLine(today) {
  if (!today) return ''
  const ad = new Date(today.ad_date + 'T00:00:00')
  const adStr = ad.toLocaleDateString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
  return `${today.bs_month_name} ${today.bs.day}, ${today.bs.year} BS  ·  ${adStr}`
}

export default function Header({
  calendar,
  today,
  lang,
  onPrev,
  onNext,
  onToday,
  onToggleLang,
  onAdd,
  onPreviewReminders,
  onOpenSettings,
  notif,
}) {
  const channels = []
  if (notif?.email?.active) channels.push('email')
  if (notif?.sms?.active) channels.push('SMS')
  const reminderTitle = channels.length
    ? `Reminders on via ${channels.join(' + ')} → preview what would go out`
    : 'No delivery channel set yet — click the gear to add an email or phone'
  const monthTitle = calendar
    ? lang === 'np'
      ? `${BS_MONTHS_NP[calendar.bs_month - 1]} ${toNepaliDigits(calendar.bs_year)}`
      : `${BS_MONTHS_EN[calendar.bs_month - 1]} ${calendar.bs_year}`
    : '…'

  const adSpan = calendar
    ? `${fmt(calendar.month_start_ad)} – ${fmt(calendar.month_end_ad)}`
    : ''

  return (
    <header className="header">
      <div className="header__brand">
        <div className="header__title">
          <span className="header__dot" /> Nepali Calendar
        </div>
        <div className="header__today">{todayLine(today)}</div>
      </div>

      <div className="header__nav">
        <button className="btn btn--icon" onClick={onPrev} aria-label="Previous month">
          ‹
        </button>
        <div className="header__month">
          <div className="header__month-name">{monthTitle}</div>
          <div className="header__month-span">{adSpan}</div>
        </div>
        <button className="btn btn--icon" onClick={onNext} aria-label="Next month">
          ›
        </button>
        <button className="btn btn--ghost" onClick={onToday}>
          Today
        </button>
      </div>

      <div className="header__actions">
        <button
          className="btn btn--ghost"
          onClick={onToggleLang}
          title="Toggle Nepali / English numerals"
        >
          {lang === 'np' ? 'अ' : 'A'}
        </button>
        <button
          className="btn btn--ghost"
          onClick={onOpenSettings}
          title="Notification settings (email / SMS)"
          aria-label="Notification settings"
        >
          ⚙️
        </button>
        <button
          className="btn btn--ghost"
          onClick={onPreviewReminders}
          title={reminderTitle}
        >
          🔔 Reminders{notif && channels.length === 0 ? ' (not set)' : ''}
        </button>
        <button className="btn btn--primary" onClick={onAdd}>
          + Add event
        </button>
      </div>
    </header>
  )
}

function fmt(iso) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
