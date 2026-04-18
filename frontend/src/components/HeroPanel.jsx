export function HeroPanel({ mode, headline, summary, stats, onRefresh, voiceUrl, onModeChange }) {
  return (
    <section className="hero-card">
      <div className="hero-top-row">
        <div>
          <div className="eyebrow light">Campus Copilot</div>
          <h1>{headline}</h1>
        </div>
        <div className="hero-mode-switch">
          <button className={mode === 'demo' ? 'active' : ''} onClick={() => onModeChange('demo')}>Demo study</button>
          <button className={mode === 'live' ? 'active' : ''} onClick={() => onModeChange('live')}>Live campus</button>
        </div>
      </div>

      <p className="hero-summary">{summary}</p>

      <div className="hero-stats-row">
        <div className="hero-stat-card">
          <span className="hero-stat-value">{stats.urgent}</span>
          <span className="hero-stat-label">urgent</span>
        </div>
        <div className="hero-stat-card">
          <span className="hero-stat-value">{stats.live}</span>
          <span className="hero-stat-label">live cards</span>
        </div>
        <div className="hero-stat-card">
          <span className="hero-stat-value">{stats.total}</span>
          <span className="hero-stat-label">total cards</span>
        </div>
      </div>

      <div className="hero-actions">
        <button className="primary-button" onClick={onRefresh}>Refresh dashboard</button>
        <a className="secondary-button" href={voiceUrl} target="_blank" rel="noreferrer">Play voice briefing</a>
      </div>
    </section>
  )
}
