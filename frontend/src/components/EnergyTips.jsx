const NAMES = {
  kitchen_kwh: 'kitchen appliances',
  laundry_kwh: 'the laundry room',
  water_heater_ac_kwh: 'the water heater and air conditioner',
  other_kwh: 'other, unmetered circuits (lighting, TV, computers, etc.)',
}
const ADVICE = {
  kitchen_kwh: 'Use lids while cooking, run the dishwasher only when full, and defrost food in the fridge.',
  laundry_kwh: 'Wash with cold water, run full loads, and air-dry when you can.',
  water_heater_ac_kwh: 'Lower the water-heater thermostat, add insulation, and set the AC a degree or two higher.',
  other_kwh: 'Switch to LED lighting and unplug devices that stay on standby.',
}

// Plain if/else rules on measured shares. These are NOT AI predictions.
export default function EnergyTips({ summary }) {
  const shares = summary.end_use_share_pct
  const ranked = Object.entries(shares).sort((a, b) => b[1] - a[1])
  const tips = ranked.slice(0, 2).map(([k, pct]) => (
    <li key={k}><strong>{NAMES[k]}: {pct.toFixed(0)}% of measured energy.</strong> {ADVICE[k]}</li>
  ))
  if (summary.avg_peak_kw > 3) tips.push(<li key="peak"><strong>Average daily peak is {summary.avg_peak_kw.toFixed(1)} kW.</strong> Avoid running several heavy appliances at the same time.</li>)
  tips.push(<li key="evening"><strong>Shift flexible chores</strong> (laundry, dishwasher) outside the evening peak if your tariff has time-of-use pricing.</li>)
  return (
    <section className="panel">
      <h2>Energy-saving suggestions <span className="tag">Rule-based, not AI</span></h2>
      <p className="hint">These suggestions come from fixed rules applied to the dataset's measured usage shares. They are not machine-learning predictions.</p>
      <ul className="tips">{tips}</ul>
    </section>
  )
}
