export const BS_MONTHS_EN = [
  'Baishakh', 'Jestha', 'Ashadh', 'Shrawan', 'Bhadra', 'Ashwin',
  'Kartik', 'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra',
]

export const BS_MONTHS_NP = [
  'वैशाख', 'जेठ', 'असार', 'साउन', 'भदौ', 'असोज',
  'कात्तिक', 'मंसिर', 'पुष', 'माघ', 'फागुन', 'चैत',
]

export const WEEKDAYS_SHORT_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
export const WEEKDAYS_SHORT_NP = ['आइत', 'सोम', 'मंगल', 'बुध', 'बिहि', 'शुक्र', 'शनि']

export const CATEGORIES = [
  { value: 'personal', label: 'Personal', color: '#3b82f6' },
  { value: 'birthday', label: 'Birthday', color: '#ec4899' },
  { value: 'anniversary', label: 'Anniversary', color: '#a855f7' },
  { value: 'meeting', label: 'Meeting', color: '#0891b2' },
  { value: 'festival', label: 'Festival', color: '#f59e0b' },
  { value: 'holiday', label: 'Holiday', color: '#dc143c' },
  { value: 'other', label: 'Other', color: '#64748b' },
]

export const CATEGORY_COLOR = Object.fromEntries(
  CATEGORIES.map((c) => [c.value, c.color]),
)

export const RECURRENCE_OPTIONS = [
  { value: 'none', label: 'One time only' },
  { value: 'yearly_ad', label: 'Every year (same English date)' },
  { value: 'yearly_bs', label: 'Every year (same Nepali date)' },
]

const NP_DIGITS = '०१२३४५६७८९'
export function toNepaliDigits(value) {
  return String(value).replace(/\d/g, (d) => NP_DIGITS[Number(d)])
}

export function daysUntilLabel(days) {
  if (days <= 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  if (days < 7) return `In ${days} days`
  if (days < 14) return 'In 1 week'
  if (days < 31) return `In ${Math.round(days / 7)} weeks`
  return `In ${Math.round(days / 30)} months`
}
