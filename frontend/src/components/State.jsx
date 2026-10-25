export function Loading({ text = 'Loading…' }) {
  return <div className="loading" role="status"><span className="spinner" />{text}</div>
}
export function ErrorBox({ message }) {
  return message ? <div className="error" role="alert">{message}</div> : null
}
