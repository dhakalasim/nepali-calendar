import { useEffect, useRef, useState } from 'react'
import { CATEGORIES, RECURRENCE_OPTIONS } from '../constants.js'

const EMPTY = {
  title: '',
  description: '',
  category: 'personal',
  recurrence: 'none',
  notify_enabled: true,
  notify_days_before: 1,
}

export default function EventModal({ mode, initial, onSave, onDelete, onClose, onConvert }) {
  const [form, setForm] = useState(() => ({
    ...EMPTY,
    ...initial,
    ad_date: initial?.ad_date || new Date().toISOString().slice(0, 10),
  }))
  const [bsPreview, setBsPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const firstField = useRef(null)

  const set = (key) => (e) => {
    const value =
      e.target.type === 'checkbox' ? e.target.checked : e.target.value
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

  const submit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return setError('Give the event a title.')
    if (!form.ad_date) return setError('Pick a date.')
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
      })
    } catch (err) {
      setError(err.message)
      setBusy(false)
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

          <div className="field-row field-row--notify">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.notify_enabled}
                onChange={set('notify_enabled')}
              />
              <span>Email me a reminder</span>
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
