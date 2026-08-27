import { CATEGORY_COLOR, toNepaliDigits } from '../constants.js'

export default function DayCell({ day, lang, onSelect, onEventClick }) {
  if (!day) return <div className="cell cell--empty" />

  const classes = ['cell']
  if (day.is_today) classes.push('cell--today')
  if (day.is_saturday) classes.push('cell--saturday')
  if (day.is_holiday) classes.push('cell--holiday')

  const bsDay = lang === 'np' ? day.bs_day_np : day.bs_day
  const adLabel =
    day.ad_day === 1 ? `${day.ad_month_name} ${day.ad_day}` : day.ad_day

  const shown = day.events.slice(0, 3)
  const extra = day.events.length - shown.length

  return (
    <div
      className={classes.join(' ')}
      onClick={() => onSelect(day)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onSelect(day)
      }}
    >
      <div className="cell__head">
        <span className="cell__bs">{bsDay}</span>
        <span className="cell__ad">{adLabel}</span>
      </div>
      <div className="cell__events">
        {shown.map((ev) => (
          <button
            key={ev.id}
            className="chip"
            style={{ '--chip': CATEGORY_COLOR[ev.category] || '#64748b' }}
            title={ev.title}
            onClick={(e) => {
              e.stopPropagation()
              onEventClick(ev.id)
            }}
          >
            {ev.title}
          </button>
        ))}
        {extra > 0 && <span className="chip chip--more">+{extra} more</span>}
      </div>
    </div>
  )
}
