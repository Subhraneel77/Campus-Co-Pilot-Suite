export function ItemCard({ item, onAction }) {
  return (
    <article className={`item-card ${item.live ? 'live' : 'demo'}`}>
      <div className="item-top-row">
        <span className={`chip chip-${item.type}`}>{item.type}</span>
        <span className={`urgency-badge ${item.urgency >= 8 ? 'danger' : item.urgency >= 6 ? 'warning' : 'calm'}`}>
          Urgency {item.urgency}/10
        </span>
      </div>

      <h3>{item.title}</h3>
      <p>{item.description}</p>

      <div className="meta-grid">
        <div>
          <span className="meta-label">Source</span>
          <span className="meta-value">{item.source}</span>
        </div>
        <div>
          <span className="meta-label">Status</span>
          <span className="meta-value">{item.status || 'Ready'}</span>
        </div>
        <div>
          <span className="meta-label">When</span>
          <span className="meta-value">{item.due_date ? item.due_date.replace('T', ' ') : 'Open-ended'}</span>
        </div>
        <div>
          <span className="meta-label">Location</span>
          <span className="meta-value">{item.location || '—'}</span>
        </div>
      </div>

      {item.actions?.length > 0 && (
        <div className="item-actions-grid">
          {item.actions.map((action) => (
            <button key={action.id} className="wide-action-button" onClick={() => onAction(item, action)}>
              {action.label}
            </button>
          ))}
        </div>
      )}

      {item.source_url && (
        <a className="source-link" href={item.source_url} target="_blank" rel="noreferrer">
          Open source reference ↗
        </a>
      )}
    </article>
  )
}
