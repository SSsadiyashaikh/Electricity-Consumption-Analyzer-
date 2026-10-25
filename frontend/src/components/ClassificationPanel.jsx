import { useState } from 'react'
import { api } from '../api'
import { Loading, ErrorBox } from './State'

const FIELDS = [
  ['peak_kw', 'Highest power in the day (kW)'],
  ['kitchen_kwh', 'Kitchen (kWh)'],
  ['laundry_kwh', 'Laundry room (kWh)'],
  ['water_heater_ac_kwh', 'Water heater + AC (kWh)'],
]

export default function ClassificationPanel() {
  const [form, setForm] = useState({ peak_kw: '', kitchen_kwh: '', laundry_kwh: '', water_heater_ac_kwh: '', daily_kwh: '', is_weekend: '0', month: '1' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    try {
      const body = { ...form }
      if (body.daily_kwh === '') delete body.daily_kwh
      setResult(await api.classify(body))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>Classify a day <span className="tag">Decision Tree</span></h2>
      <p className="hint">Enter what one day looked like. The tree predicts whether total use was Low, Medium or High.</p>
      <form onSubmit={submit}>
        <div className="fields">
          {FIELDS.map(([k, label]) => (
            <label className="field" key={k}>{label}
              <input type="number" step="any" min="0" value={form[k]} onChange={set(k)} required />
            </label>
          ))}
          <label className="field">Day type
            <select value={form.is_weekend} onChange={set('is_weekend')}>
              <option value="0">Weekday</option><option value="1">Weekend</option>
            </select>
          </label>
          <label className="field">Month
            <select value={form.month} onChange={set('month')}>
              {Array.from({ length: 12 }, (_, i) => <option key={i + 1} value={i + 1}>{new Date(2000, i, 1).toLocaleString('en', { month: 'long' })}</option>)}
            </select>
          </label>
          <label className="field">Total for the day (kWh), optional
            <input type="number" step="any" min="0" value={form.daily_kwh} onChange={set('daily_kwh')} />
          </label>
        </div>
        <button className="btn" disabled={busy}>Classify</button>
      </form>
      {busy && <Loading text="Classifying…" />}
      <ErrorBox message={error} />
      {result && (
        <div className="result">
          <p>Predicted level: <span className={`badge ${result.prediction}`}>{result.prediction}</span></p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Level</th><th>Tree confidence</th></tr></thead>
              <tbody>{Object.entries(result.probabilities).map(([k, v]) => <tr key={k}><td>{k}</td><td>{(v * 100).toFixed(1)}%</td></tr>)}</tbody>
            </table>
          </div>
          <p className="hint">Thresholds learned from training days: Low below {result.thresholds_kwh.low_max.toFixed(1)} kWh, High from {result.thresholds_kwh.high_min.toFixed(1)} kWh.
            {result.threshold_label_for_daily_kwh && <> Your total of {form.daily_kwh} kWh falls in the <strong>{result.threshold_label_for_daily_kwh}</strong> band.</>}</p>
          <p className="hint">{result.note}</p>
        </div>
      )}
    </section>
  )
}
