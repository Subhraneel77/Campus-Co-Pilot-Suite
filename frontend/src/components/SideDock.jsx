export function SideDock() {
  const openPortal = (hash) => {
    const url = `${window.location.origin}${window.location.pathname}${hash}`
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="side-dock">
      <button className="dock-btn" onClick={() => openPortal('#/memory')}>Memory</button>
      <button className="dock-btn" onClick={() => openPortal('#/setup')}>Setup</button>
    </div>
  )
}
