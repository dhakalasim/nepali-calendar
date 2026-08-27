import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

const BLANK = {
  notify_emails: '',
  notify_phones: '',
  email_enabled: true,
  sms_enabled: false,
}

export default function SettingsModal({ status, onClose, onSaved, flash }) {
  const [form, setForm] = useState(BLANK)
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [testResult, setTestResult] = useState({})
  const firstField = useRef(null)

  useEffect(() => {
    api
      .getNotifSettings()
      .then((s) => setForm({ ...BLANK, ...s }))
      .catch((e) => setError(e.message))
      .finally(() => setLoaded(true))
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    if (loaded) firstField.current?.focus()
  }, [loaded])

  const set = (key) => (e) =>
    setForm((f) => ({
      ...f,
      [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value,
    }))

  const persist = async () => {
    return api.updateNotifSettings({
      notify_emails: form.notify_emails,
      notify_phones: form.notify_phones,
      email_enabled: form.email_enabled,
      sms_enabled: form.sms_enabled,
    })
  }

  const save = async () => {
    setBusy('save')
    setError('')
    try {
      await persist()
      await onSaved()
      flash('Notification settings saved')
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  const test = async (channel) => {
    setBusy(channel)
    setError('')
    setTestResult((r) => ({ ...r, [channel]: null }))
    try {
      await persist()
      const res = await api.sendTest([channel])
      setTestResult((r) => ({ ...r, [channel]: res.channels[channel] }))
      await onSaved()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  const email = status?.email
  const sms = status?.sms

  return (
    <div className="overlay" onMouseDown={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="modal__head">
          <h2>Notification settings</h2>
          <button className="btn btn--icon" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="modal__body">
          {!loaded && <p className="panel__empty">Loading…</p>}

          {loaded && (
            <>
              {/* -------- Email -------- */}
              <div className="channel">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={form.email_enabled}
                    onChange={set('email_enabled')}
                  />
                  <span>Email reminders</span>
                </label>
                <label className="field">
                  <span>Send to (comma-separated)</span>
                  <input
                    ref={firstField}
                    type="text"
                    value={form.notify_emails}
                    onChange={set('notify_emails')}
                    placeholder="you@example.com"
                  />
                </label>
                <ProviderHint
                  ok={email?.provider_configured}
                  okText="SMTP is connected — real emails will be sent."
                  offText="Not connected — emails only print to the backend console. Add SMTP_* to .env (Gmail app password) and restart the backend."
                />
                <TestRow
                  label="Send test email"
                  busy={busy === 'email'}
                  result={testResult.email}
                  onClick={() => test('email')}
                />
              </div>

              {/* -------- SMS -------- */}
              <div className="channel">
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={form.sms_enabled}
                    onChange={set('sms_enabled')}
                  />
                  <span>Text message (SMS) reminders</span>
                </label>
                <label className="field">
                  <span>Phone number(s), international format</span>
                  <input
                    type="text"
                    value={form.notify_phones}
                    onChange={set('notify_phones')}
                    placeholder="+9779800000000"
                  />
                </label>
                <ProviderHint
                  ok={sms?.provider_configured}
                  okText={`SMS gateway connected (${sms?.provider}) — real texts will be sent.`}
                  offText="Not connected — texts only print to the backend console. Add a Nepal SMS gateway token (AakashSMS or Sparrow) to .env and restart the backend."
                />
                <TestRow
                  label="Send test text"
                  busy={busy === 'sms'}
                  result={testResult.sms}
                  onClick={() => test('sms')}
                />
              </div>

              <p className="hint">
                The daily digest runs at{' '}
                <strong>{String(status?.notify_hour ?? 7).padStart(2, '0')}:00</strong>{' '}
                Nepal time. How far ahead each reminder fires is set per event
                ("days before").
              </p>

              {error && <div className="modal__error">{error}</div>}

              <div className="modal__foot">
                <span />
                <div className="modal__foot-right">
                  <button className="btn btn--ghost" onClick={onClose}>
                    Cancel
                  </button>
                  <button
                    className="btn btn--primary"
                    onClick={save}
                    disabled={busy === 'save'}
                  >
                    {busy === 'save' ? 'Saving…' : 'Save'}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function ProviderHint({ ok, okText, offText }) {
  return (
    <div className={`hint ${ok ? 'hint--ok' : 'hint--warn'}`}>
      {ok ? '✓ ' : '! '}
      {ok ? okText : offText}
    </div>
  )
}

function TestRow({ label, busy, result, onClick }) {
  return (
    <div className="test-row">
      <button className="btn btn--ghost btn--sm" onClick={onClick} disabled={busy}>
        {busy ? 'Sending…' : label}
      </button>
      {result && (
        <span className={`test-result test-result--${result.status}`}>
          {result.status === 'sent' && `sent → ${result.detail}`}
          {result.status === 'logged' && 'printed to backend console'}
          {result.status === 'skipped' && result.detail}
          {result.status === 'failed' && `failed: ${result.detail}`}
        </span>
      )}
    </div>
  )
}
