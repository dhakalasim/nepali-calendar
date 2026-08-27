import DayCell from './DayCell.jsx'
import { WEEKDAYS_SHORT_EN, WEEKDAYS_SHORT_NP } from '../constants.js'

export default function CalendarGrid({ calendar, lang, onSelectDay, onEventClick }) {
  if (!calendar) return <div className="grid grid--loading">Loading calendar…</div>

  const weekdays = lang === 'np' ? WEEKDAYS_SHORT_NP : WEEKDAYS_SHORT_EN
  const leading = Array.from({ length: calendar.start_weekday }, () => null)
  const cells = [...leading, ...calendar.days]
  while (cells.length % 7 !== 0) cells.push(null)

  return (
    <div className="grid">
      <div className="grid__weekdays">
        {weekdays.map((w, i) => (
          <div key={w} className={`grid__weekday${i === 6 ? ' grid__weekday--sat' : ''}`}>
            {w}
          </div>
        ))}
      </div>
      <div className="grid__days">
        {cells.map((day, i) => (
          <DayCell
            key={day ? day.ad_date : `empty-${i}`}
            day={day}
            lang={lang}
            onSelect={onSelectDay}
            onEventClick={onEventClick}
          />
        ))}
      </div>
    </div>
  )
}
