export default function StatCard({ label, value, unit, note }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value">{value}{unit && <span className="unit">{unit}</span>}</div>
      {note && <div className="note">{note}</div>}
    </div>
  )
}
