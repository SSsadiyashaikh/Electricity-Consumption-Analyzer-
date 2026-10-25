import { useEffect, useState } from 'react'
import { api } from './api'
import Sidebar from './components/Sidebar'
import StatCard from './components/StatCard'
import ConsumptionChart from './components/ConsumptionChart'
import PredictionPanel from './components/PredictionPanel'
import ClassificationPanel from './components/ClassificationPanel'
import ClusterPanel from './components/ClusterPanel'
import EnergyTips from './components/EnergyTips'
import ModelPerformance from './components/ModelPerformance'
import { Loading, ErrorBox } from './components/State'

const TITLES = {
  overview: 'Overview', forecast: 'Forecast', classify: 'Classify a day',
  clusters: 'Usage clusters', models: 'Model performance', tips: 'Energy tips',
}
const kwh = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })

export default function App() {
  const [view, setView] = useState('overview')
  const [data, setData] = useState({ summary: null, monthly: null, metrics: null })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    const load = async (key, fn) => {
      try { const v = await fn(); if (alive) setData((d) => ({ ...d, [key]: v })) }
      catch (err) { if (alive) setErrors((e) => ({ ...e, [key]: err.message })) }
    }
    Promise.all([load('summary', api.summary), load('monthly', api.monthly), load('metrics', api.metrics)])
      .finally(() => alive && setLoading(false))
    return () => { alive = false }
  }, [])

  const { summary, monthly, metrics } = data
  const firstError = errors.summary || errors.monthly

  return (
    <div className="shell">
      <Sidebar view={view} onChange={setView} />
      <main className="main">
        <header>
          <h1>{TITLES[view]}</h1>
          {summary && <p>Measured household data, {summary.first_day} to {summary.last_day} ({summary.usable_days} usable days).</p>}
        </header>
   
        {loading && <Loading text="Loading data from the backend…" />}

        {view === 'overview' && (<>
          <ErrorBox message={firstError} />
          {summary && (
            <div className="stats">
              <StatCard label="Total energy" value={kwh(summary.total_kwh)} unit="kWh" note="usable days only" />
              <StatCard label="Average per day" value={summary.avg_daily_kwh.toFixed(1)} unit="kWh" />
              <StatCard label="Average daily peak" value={summary.avg_peak_kw.toFixed(2)} unit="kW" />
              {summary.highest_month && <StatCard label="Highest complete month" value={kwh(summary.highest_month.kwh)} unit="kWh" note={summary.highest_month.month} />}
              <StatCard label="Highest day" value={summary.highest_day.kwh.toFixed(1)} unit="kWh" note={summary.highest_day.date} />
            </div>
          )}
          {monthly && <ConsumptionChart monthly={monthly.data} />}
        </>)}

        {view === 'forecast' && <PredictionPanel />}
        {view === 'classify' && <ClassificationPanel />}
        {view === 'clusters' && (<><ErrorBox message={errors.metrics} /><ClusterPanel metrics={metrics} /></>)}
        {view === 'models' && (<><ErrorBox message={errors.metrics} />{metrics && <ModelPerformance metrics={metrics} />}</>)}
        {view === 'tips' && (<><ErrorBox message={errors.summary} />{summary && <EnergyTips summary={summary} />}</>)}
      </main>
    </div>
  )
}
