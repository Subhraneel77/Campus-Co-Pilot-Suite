function StatusRow({ label, value, positiveText = 'Connected', negativeText = 'Not configured' }) {
  const good = Boolean(value)
  return (
    <div className="setup-row">
      <div>
        <div className="setup-label">{label}</div>
        <div className="setup-note">{good ? positiveText : negativeText}</div>
      </div>
      <span className={`status-dot ${good ? 'on' : 'off'}`}></span>
    </div>
  )
}

export function SetupPanel({ setup }) {
  return (
    <div className="stack">
      <div className="section-head">
        <div>
          <div className="eyebrow">Setup</div>
          <h2>Integration checklist</h2>
        </div>
        <div className="muted-badge">server status</div>
      </div>

      <div className="setup-card-grid">
        <div className="setup-card">
          <h3>Assistant stack</h3>
          <StatusRow label="Dify Chatflow" value={setup?.dify_configured} positiveText="Conversational planner is ready" />
          <StatusRow label="ElevenLabs" value={setup?.elevenlabs_configured} positiveText="Voice input/output is ready" />
        </div>

        <div className="setup-card">
          <h3>Memory</h3>
          <StatusRow label="Cognee" value={setup?.cognee_enabled} positiveText="Persistent memory enabled" negativeText="Optional memory is still off" />
        </div>

        <div className="setup-card">
          <h3>Live defaults</h3>
          <div className="setup-note">Campus ID: {setup?.default_campus_id}</div>
          <div className="setup-note">Canteen: {setup?.default_canteen_id}</div>
          <div className="setup-note">Location query: {setup?.default_location_query}</div>
        </div>
      </div>

      <div className="answer-card">
        <div className="meta-label">Recommended demo flow</div>
        <div className="answer-copy">1. Open Demo study mode to show deadline rescue and opportunity registration. 2. Switch to Live campus mode to show public TUM room, map, and Mensa data. 3. Use the Assistant tab to explain why one of those cards should be your next action.</div>
      </div>
    </div>
  )
}
