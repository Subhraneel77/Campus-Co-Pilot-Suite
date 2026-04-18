import { useEffect, useMemo, useState } from 'react'
import { fetchCopilotHome, fetchSetupStatus, getBriefingVoiceUrl } from './api'
import { UnifiedAssistantPanel } from './components/UnifiedAssistantPanel'
import { MemoryView } from './components/MemoryView'
import { SetupView } from './components/SetupView'
import { SideDock } from './components/SideDock'
import './styles.css'

function MainCopilot() {
  const [home, setHome] = useState(null)
  const [setup, setSetup] = useState(null)
  const [busy, setBusy] = useState(true)
  const [toast, setToast] = useState('')

  async function refresh() {
    setBusy(true)
    try {
      const [homeData, setupData] = await Promise.all([
        fetchCopilotHome(),
        fetchSetupStatus(),
      ])
      setHome(homeData)
      setSetup(setupData)
    } catch (error) {
      setToast(error.message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(''), 3200)
    return () => clearTimeout(timer)
  }, [toast])

  const voiceUrl = useMemo(() => getBriefingVoiceUrl(), [])

  function handleAction(item, action) {
    window.open(action.url, '_blank', 'noopener,noreferrer')
    setToast(`${action.label} launched for “${item.title}”.`)
  }

  return (
    <div className="shell unified-shell">
      <div className="aurora aurora-a"></div>
      <div className="aurora aurora-b"></div>
      <SideDock />

      <main className="app-frame unified-frame">
        <section className="welcome-banner">
          <div>
            <div className="eyebrow light">🚀 Campus Co-Pilot Suite</div>
            <h1>Your Unified Assistant for Study, Campus Life, & Memory 🧠</h1>
            <p>
              Launch your intelligent assistant to discover today’s crucial updates. Take immediate action from a centralized hub — seamlessly integrated with Google Calendar 📅, Gmail 📧, Maps 🗺️, and public campus utilities 🏢.
            </p>
          </div>
          <div className="welcome-actions">
            <button className="primary-button" onClick={refresh}>🔄 Sync Updates</button>
            <a className="secondary-button" href={voiceUrl} target="_blank" rel="noreferrer">▶️ Play Welcome Briefing</a>
          </div>
        </section>

        {toast && <div className="toast">{toast}</div>}

        {busy ? (
          <section className="content-card"><div className="loader-card">Loading your assistant workspace...</div></section>
        ) : (
          <section className="content-card unified-content">
            <UnifiedAssistantPanel
              home={home}
              onAction={handleAction}
              onToast={setToast}
              onRefresh={refresh}
              setup={setup}
            />
          </section>
        )}
      </main>
    </div>
  )
}

export default function App() {
  const hash = window.location.hash || '#/'

  if (hash.startsWith('#/memory')) return <MemoryView />
  if (hash.startsWith('#/setup')) return <SetupView />
  return <MainCopilot />
}
