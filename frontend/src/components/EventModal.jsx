import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CATEGORIES,
  RECURRENCE_OPTIONS,
  REMINDER_CHANNELS,
  REMINDER_CHANNEL_VALUES,
  formatNepalDateTime,
  isoToNepalInput,
} from '../constants.js'

const EMPTY = {
  title: '',
  description: '',
  category: 'personal',
  recurrence: 'none',
  notify_enabled: true,
  notify_days_before: 1,
}

let rowSeq = 0
const newRow = (patch = {}) => ({
  key: `r${++rowSeq}`,
  remind_at: '',
  channels: 'all',
  status: 'pending',
  sent_at: null,
  iso: null,
  ...patch,
})

export default function EventModal({
  mode,
  initial,
  onSave,
  onDelete,
  onClose,
  onConvert,
  onSendNow,
}) {
  const [form, setForm] = useState(() => ({
    ...EMPTY,
    ...initial,
    ad_date: initial?.ad_date || new Date().toISOString().slice(0, 10),
  }))
  const [rows, setRows] = useState(() =>
    (initial?.reminders || []).map((r) =>
      newRow({
        id: r.id,
        remind_at: isoToNepalInput(r.remind_at),
        channels: REMINDER_CHANNEL_VALUES.includes(r.channels) ? r.channels : 'all',
        status: r.status,
        sent_at: r.sent_at,
        iso: r.remind_at,
      }),
    ),
  )
  const [sendNowChannel, setSendNowChannel] = useState('all')
  const [sendNowMsg, setSendNowMsg] = useState('')
  const [bsPreview, setBsPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const firstField = useRef(null)

  const set = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [key]: value }))
  }

  useEffect(() => {
    firstField.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    let cancelled = false
    if (!form.ad_date) return
    onConvert({ ad_date: form.ad_date })
      .then((r) => !cancelled && setBsPreview(r))
      .catch(() => !cancelled && setBsPreview(null))
    return () => {
      cancelled = true
    }
  }, [form.ad_date, onConvert])

  const pendingRows = useMemo(() => rows.filter((r) => !r.sent_at), [rows])
  const sentRows = useMemo(() => rows.filter((r) => r.sent_at), [rows])

  const patchRow = (key, patch) =>
    setRows((rs) => rs.map((r) => (r.key === key ? { ...r, ...patch } : r)))
  const removeRow = (key) => setRows((rs) => rs.filter((r) => r.key !== key))
  const addRow = () => setRows((rs) => [...rs, newRow()])

  const submit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return setError('Give the event a title.')
    if (!form.ad_date) return setError('Pick a date.')
    if (pendingRows.some((r) => !r.remind_at))
      return setError('Every reminder time needs a date and time (or remove the empty row).')
    setBusy(true)
    setError('')
    try {
      await onSave({
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category,
        recurrence: form.recurrence,
        notify_enabled: form.notify_enabled,
        notify_days_before: Number(form.notify_days_before) || 0,
        ad_date: form.ad_date,
        reminders: pendingRows.map((r) => ({
          remind_at: r.remind_at,
          channels: r.channels,
        })),
      })
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  const sendNow = async () => {
    setSendNowMsg('Sending…')
    try {
      const res = await onSendNow(initial.id, sendNowChannel)
      if (!res.sent) {
        setSendNowMsg(res.note || 'Nothing sent — check recipients in ⚙️ settings.')
      } else {
        const parts = Object.entries(res.channels).map(
          ([c, v]) => `${c}: ${v.status === 'sent' ? 'sent' : v.status}`,
        )
        setSendNowMsg(`Sent — ${parts.join(', ')}`)
      }
    } catch (err) {
      setSendNowMsg(err.message)
    }
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="modal__head">
          <h2>{mode === 'edit' ? 'Edit event' : 'New event'}</h2>
          <button className="btn btn--icon" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <form className="modal__body" onSubmit={submit}>
          <label className="field">
            <span>Title</span>
            <input
              ref={firstField}
              value={form.title}
              onChange={set('title')}
              placeholder="e.g. Aama's birthday"
              maxLength={200}
            />
          </label>

          <label className="field">
            <span>Notes</span>
            <textarea
              value={form.description}
              onChange={set('description')}
              rows={2}
              placeholder="Optional"
            />
          </label>

          <div className="field-row">
            <label className="field">
              <span>Date (English / AD)</span>
              <input type="date" value={form.ad_date} onChange={set('ad_date')} />
            </label>
            <label className="field">
              <span>Category</span>
              <select value={form.category} onChange={set('category')}>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="bs-preview">
            {bsPreview
              ? `Nepali date: ${bsPreview.bs_month_name} ${bsPreview.bs.day}, ${bsPreview.bs.year} (${bsPreview.weekday_name})`
              : 'Nepali date: …'}
          </div>

          <label className="field">
            <span>Repeat</span>
            <select value={form.recurrence} onChange={set('recurrence')}>
              {RECURRENCE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>

          <fieldset className="reminders">
            <legend>Reminders</legend>

            <div className="field-row field-row--notify">
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={form.notify_enabled}
                  onChange={set('notify_enabled')}
                />
                <span>Auto reminder (in the daily digest)</span>
              </label>
              <label className="field field--narrow">
                <span>Days before</span>
                <input
                  type="number"
                  min={0}
                  max={365}
                  value={form.notify_days_before}
                  onChange={set('notify_days_before')}
                  disabled={!form.notify_enabled}
                />
              </label>
            </div>

            <div className="reminders__exact">
              <span className="reminders__label">At a specific time (Nepal time)</span>

              {sentRows.map((r) => (
                <div key={r.key} className="reminder-row reminder-row--sent">
                  <span>✓ sent · {formatNepalDateTime(r.iso)}</span>
                </div>
              ))}

              {pendingRows.map((r) => (
                <div key={r.key} className="reminder-row">
                  <input
                    type="datetime-local"
                    value={r.remind_at}
                    onChange={(e) => patchRow(r.key, { remind_at: e.target.value })}
                  />
                  <select
                    value={r.channels}
                    onChange={(e) => patchRow(r.key, { channels: e.target.value })}
                  >
                    {REMINDER_CHANNELS.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btn btn--icon btn--sm"
                    onClick={() => removeRow(r.key)}
                    aria-label="Remove reminder"
                  >
                    ×
                  </button>
                </div>
              ))}

              <button type="button" className="btn btn--ghost btn--sm" onClick={addRow}>
                ＋ Add a time
              </button>
            </div>

            {mode === 'edit' && (
              <div className="send-now">
                <select
                  value={sendNowChannel}
                  onChange={(e) => setSendNowChannel(e.target.value)}
                >
                  {REMINDER_CHANNELS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
                <button type="button" className="btn btn--ghost btn--sm" onClick={sendNow}>
                  Send reminder now
                </button>
                {sendNowMsg && <span className="hint">{sendNowMsg}</span>}
              </div>
            )}
          </fieldset>

          {error && <div className="modal__error">{error}</div>}

          <div className="modal__foot">
            {mode === 'edit' ? (
              <button
                type="button"
                className="btn btn--danger"
                onClick={() => onDelete(initial.id)}
              >
                Delete
              </button>
            ) : (
              <span />
            )}
            <div className="modal__foot-right">
              <button type="button" className="btn btn--ghost" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn btn--primary" disabled={busy}>
                {busy ? 'Saving…' : mode === 'edit' ? 'Save changes' : 'Add event'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
