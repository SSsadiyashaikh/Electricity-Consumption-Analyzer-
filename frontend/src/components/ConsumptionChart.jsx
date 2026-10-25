import { ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const fmt = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 })

export default function ConsumptionChart({ monthly }) {
  const complete = monthly.filter((m) => m.complete)
  const skipped = monthly.length - complete.length
  return (
    <div className="grid-2">
      <section className="panel">
        <h2>Monthly consumption</h2>
        <p className="hint">Total kWh per month, from minute-level readings. Months with under 90% of days measured are left out ({skipped} left out).</p>
        <div className="chart-box">
          <ResponsiveContainer>
            <LineChart data={complete} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="#e3e9ee" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={24} />
              <YAxis tick={{ fontSize: 11 }} width={48} />
              <Tooltip formatter={(v) => [`${fmt(v)} kWh`, 'Total']} />
              <Line type="monotone" dataKey="total_kwh" stroke="#e89b00" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="panel">
        <h2>Average daily use by month</h2>
        <p className="hint">Mean kWh per measured day, so partial months compare fairly.</p>
        <div className="chart-box">
          <ResponsiveContainer>
            <BarChart data={monthly} margin={{ left: 0, right: 12, top: 8 }}>
              <CartesianGrid stroke="#e3e9ee" vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={24} />
              <YAxis tick={{ fontSize: 11 }} width={40} />
              <Tooltip formatter={(v) => [`${fmt(v)} kWh/day`, 'Average']} />
              <Bar dataKey="avg_daily_kwh" fill="#1f7f86" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}
