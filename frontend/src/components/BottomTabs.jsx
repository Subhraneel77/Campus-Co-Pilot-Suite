export function BottomTabs({ tabs, active, onChange }) {
  return (
    <nav className="bottom-tabs">
      {tabs.map((tab) => (
        <button key={tab} className={active === tab ? 'active' : ''} onClick={() => onChange(tab)}>
          {tab}
        </button>
      ))}
    </nav>
  )
}
