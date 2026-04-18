export function PriorityCard({ item, actionLabel, onAction }) {
  const urgencyClass = item.urgency >= 8 ? 'danger' : item.urgency >= 6 ? 'warning' : 'calm'

  return (
    <article className="priority-card">
      <div className="card-header-row">
        <span className={`chip chip-${item.type}`}>{item.type}</span>
        <span className={`urgency-badge ${urgencyClass}`}>Urgency {item.urgency}/10</span>
      </div>

      <h3>{item.title}</h3>
      <p>{item.description}</p>

      <div className="meta-grid">
        <div>
          <span className="meta-label">Source</span>
          <span className="meta-value">{item.source}</span>
        </div>
        <div>
          <span className="meta-label">Due</span>
          <span className="meta-value">{item.due_date || 'No fixed date'}</span>
        </div>
        <div className="meta-span-2">
          <span className="meta-label">Suggested action</span>
          <span className="meta-value">{item.suggested_action}</span>
        </div>
      </div>

      <button className="wide-action-button" onClick={onAction}>{actionLabel}</button>
    </article>
  )
}
