import { useState } from 'react'
import { api } from '../api'
import { Loading, ErrorBox } from './State'

export default function ClusterPanel({ metrics }) {
  const [form, setForm] = useState({ daily_kwh: '', peak_kw: '', evening_share_pct: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const km = metrics && metrics.kmeans

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    try { setResult(await api.cluster(form)) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  return (
    <section className="panel">
      <h2>Usage clusters <span className="tag">K-Means</span></h2>
      <p className="hint">Find which group of historical days a day most resembles.</p>
      <form onSubmit={submit}>
        <div className="fields">
          <label className="field">Total for the day (kWh)
            <input type="number" step="any" min="0" value={form.daily_kwh} onChange={set('daily_kwh')} required /></label>
          <label className="field">Highest power in the day (kW)
            <input type="number" step="any" min="0" value={form.peak_kw} onChange={set('peak_kw')} required /></label>
          <label className="field">Share used 6 pm–midnight (%)
            <input type="number" step="any" min="0" max="100" value={form.evening_share_pct} onChange={set('evening_share_pct')} required /></label>
        </div>
        <button className="btn" disabled={busy}>Find my cluster</button>
      </form>
      {busy && <Loading text="Assigning cluster…" />}
      <ErrorBox message={error} />
      {result && result.profile && (
        <div className="result">
          <p>This day belongs to <strong>cluster {result.cluster}</strong>: {result.profile.description}.</p>
          <p className="hint">Average of {result.profile.days} historical days in this cluster: {result.profile.means.daily_kwh.toFixed(1)} kWh/day, peak {result.profile.means.peak_kw.toFixed(2)} kW, {result.profile.means.evening_share_pct.toFixed(0)}% in the evening. Distance to cluster centre: {result.distance_to_centre} (standardized units).</p>
        </div>
      )}
      {km && (
        <div className="result">
          <h3>All clusters (measured on training days)</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Cluster</th><th>Days</th><th>kWh/day</th><th>Peak kW</th><th>Evening %</th><th>Weekend days %</th></tr></thead>
              <tbody>{km.profiles.map((p) => (
                <tr key={p.cluster}><td>{p.cluster}</td><td>{p.days}</td><td>{p.means.daily_kwh.toFixed(1)}</td>
                  <td>{p.means.peak_kw.toFixed(2)}</td><td>{p.means.evening_share_pct.toFixed(0)}</td><td>{p.weekend_share_pct.toFixed(0)}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
