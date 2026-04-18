export function DashboardControls({ mode, controls, onChange, onApply }) {
  if (mode !== 'live') {
    return (
      <section className="controls-card">
        <div>
          <div className="eyebrow">Demo safeguard</div>
          <h3>Authentic academic mock profile</h3>
          <p>Because you do not have a TUM student login, Demo mode keeps your study planning realistic with believable courses, deadlines, and opportunity cards.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="controls-card live-grid">
      <div className="control-block">
        <label>Campus</label>
        <select value={controls.selectedCampusId || ''} onChange={(e) => onChange('selectedCampusId', e.target.value)}>
          {(controls.campusOptions || []).map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="control-block">
        <label>Canteen</label>
        <select value={controls.selectedCanteenId || ''} onChange={(e) => onChange('selectedCanteenId', e.target.value)}>
          {(controls.canteenOptions || []).map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className="control-block control-wide">
        <label>Location query</label>
        <input
          value={controls.selectedLocationQuery || ''}
          onChange={(e) => onChange('selectedLocationQuery', e.target.value)}
          placeholder="Try garching, stammgelaende, sw3..."
        />
      </div>

      <button className="primary-button control-apply" onClick={onApply}>Apply live filters</button>
    </section>
  )
}
