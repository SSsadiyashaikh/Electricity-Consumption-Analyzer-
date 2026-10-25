const f = (v, d = 3) => Number(v).toFixed(d)

export default function ModelPerformance({ metrics }) {
  const lr = metrics.linear_regression, dt = metrics.decision_tree, km = metrics.kmeans
  return (
    <>
      <section className="panel">
        <h2>Linear Regression <span className="tag">forecast</span></h2>
        <p className="hint">Trained {lr.train_period[0]} to {lr.train_period[1]}; tested on {lr.test_period[0]} to {lr.test_period[1]} ({lr.test_rows} unseen days).</p>
        <div className="table-wrap"><table>
          <thead><tr><th>Model</th><th>MAE (kWh)</th><th>RMSE (kWh)</th><th>R²</th></tr></thead>
          <tbody>
            <tr><td>Linear Regression</td><td>{f(lr.test_metrics.mae)}</td><td>{f(lr.test_metrics.rmse)}</td><td>{f(lr.test_metrics.r2)}</td></tr>
            <tr><td>Baseline: same as yesterday</td><td>{f(lr.baseline_yesterday_metrics.mae)}</td><td>{f(lr.baseline_yesterday_metrics.rmse)}</td><td>{f(lr.baseline_yesterday_metrics.r2)}</td></tr>
          </tbody></table></div>
      </section>
      <section className="panel">
        <h2>Decision Tree <span className="tag">Low / Medium / High</span></h2>
        <p className="hint">{dt.threshold_method} Cut-offs: {f(dt.thresholds_kwh.low_max, 1)} and {f(dt.thresholds_kwh.high_min, 1)} kWh. {dt.note}</p>
        <p>Accuracy {f(dt.accuracy)} · macro precision {f(dt.macro.precision)} · macro recall {f(dt.macro.recall)} · macro F1 {f(dt.macro.f1)}</p>
        <div className="table-wrap"><table>
          <thead><tr><th>Level</th><th>Precision</th><th>Recall</th><th>F1</th><th>Test days</th></tr></thead>
          <tbody>{Object.entries(dt.per_class).map(([k, v]) => (
            <tr key={k}><td>{k}</td><td>{f(v.precision)}</td><td>{f(v.recall)}</td><td>{f(v.f1)}</td><td>{dt.test_class_counts[k]}</td></tr>))}</tbody></table></div>
        <h3 style={{ marginTop: '1rem' }}>Confusion matrix (rows: actual, columns: predicted)</h3>
        <div className="table-wrap"><table className="cm">
          <thead><tr><th></th>{dt.confusion_matrix.labels.map((l) => <th key={l}>{l}</th>)}</tr></thead>
          <tbody>{dt.confusion_matrix.matrix.map((row, i) => (
            <tr key={i}><th>{dt.confusion_matrix.labels[i]}</th>{row.map((v, j) => <td key={j} className={i === j ? 'diag' : ''}>{v}</td>)}</tr>))}</tbody></table></div>
      </section>
      <section className="panel">
        <h2>K-Means <span className="tag">clusters</span></h2>
        <p className="hint">{km.selection_rule}. Chosen k = {km.chosen_k}. Inertia {f(km.inertia, 1)}, silhouette {f(km.silhouette_train)} (training) and {f(km.silhouette_test)} (test).</p>
        <div className="table-wrap"><table>
          <thead><tr><th>k</th><th>Inertia</th><th>Silhouette</th></tr></thead>
          <tbody>{km.k_scores.map((s) => <tr key={s.k}><td>{s.k}</td><td>{f(s.inertia, 1)}</td><td>{f(s.silhouette)}</td></tr>)}</tbody></table></div>
      </section>
    </>
  )
}
