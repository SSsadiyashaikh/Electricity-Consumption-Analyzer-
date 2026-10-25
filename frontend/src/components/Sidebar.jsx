const ITEMS = [
  ['overview', 'Overview'],
  ['forecast', 'Forecast'],
  ['classify', 'Classify a day'],
  ['clusters', 'Usage clusters'],
  ['models', 'Model performance'],
  ['tips', 'Energy tips'],
]

export default function Sidebar({ view, onChange }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        Electricity Analyzer
        <small>Household energy, UCI dataset</small>
      </div>
      <nav className="nav" aria-label="Main">
        {ITEMS.map(([id, label]) => (
          <button key={id} aria-current={view === id ? 'page' : undefined} onClick={() => onChange(id)}>
            {label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
