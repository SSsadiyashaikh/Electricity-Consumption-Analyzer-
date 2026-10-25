import { useState } from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { api } from '../api'
import { Loading, ErrorBox } from './State'

export default function PredictionPanel() {
  const [days, setDays] = useState(7)
  const [own, setOwn] = useState(false)
  const [recent, setRecent] = useState(Array(7).fill(''))
  const [startDate, setStartDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const setRecentAt = (i, v) => setRecent(recent.map((x, j) => (j === i ? v : x)))

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    try {
      const body = { days_ahead: Number(days) }
      if (own) {
        body.recent_daily_kwh = recent.map(Number)
        body.start_date = startDate
      }
      setResult(await api.predict(body))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>Forecast daily consumption <span className="tag">Linear Regression</span></h2>
      <p className="hint">Forecasts kWh per day from the previous 7 days and the calendar. By default it starts from the last usable week in the dataset.</p>
      <form onSubmit={submit}>
        <div className="fields">
          <label className="field">Days to forecast (1–30)
            <input type="number" min="1" max="30" value={days} onChange={(e) => setDays(e.target.value)} required />
          </label>
        </div>
        <label className="check">
          <input type="checkbox" checked={own} onChange={(e) => setOwn(e.target.checked)} />
          Use my own last 7 days of usage instead
        </label>
        {own && (
          <div className="fields">
            {recent.map((v, i) => (
              <label className="field" key={i}>Day {i + 1} of 7 (kWh, oldest first)
                <input type="number" step="any" min="0" value={v} onChange={(e) => setRecentAt(i, e.target.value)} required />
              </label>
            ))}
            <label className="field">First day to forecast
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
            </label>
          </div>
        )}
        <button className="btn" disabled={busy}>Run forecast</button>
      </form>
      {busy && <Loading text="Forecasting…" />}
      <ErrorBox message={error} />
      {result && (
        <div className="result">
          <p className="hint">Based on {result.based_on}. {result.note}</p>
          <div className="chart-box">
            <ResponsiveContainer>
              <LineChart data={result.predictions} margin={{ left: 0, right: 12, top: 8 }}>
                <CartesianGrid stroke="#e3e9ee" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={20} />
                <YAxis tick={{ fontSize: 11 }} width={44} />
                <Tooltip formatter={(v) => [`${v} kWh`, 'Predicted']} />
                <Line type="monotone" dataKey="predicted_kwh" stroke="#e89b00" strokeWidth={2.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Predicted kWh</th></tr></thead>
              <tbody>{result.predictions.map((p) => <tr key={p.date}><td>{p.date}</td><td>{p.predicted_kwh}</td></tr>)}</tbody>
            </table>
          </div>
          {result.test_metrics && (
            <p className="hint">Held-out test accuracy of this model: MAE {result.test_metrics.mae.toFixed(2)} kWh, RMSE {result.test_metrics.rmse.toFixed(2)} kWh, R² {result.test_metrics.r2.toFixed(3)}.</p>
          )}
        </div>
      )}
    </section>
  )
}
