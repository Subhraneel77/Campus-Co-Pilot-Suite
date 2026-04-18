import { useEffect, useState } from 'react'
import { fetchSetupStatus } from '../api'

export function SetupView() {
  const [setup, setSetup] = useState(null)

  useEffect(() => {
    fetchSetupStatus().then(setSetup).catch(() => setSetup(null))
  }, [])

  return (
    <div className="portal-page">
      <div className="portal-card">
        <div className="eyebrow">Setup</div>
        <h1>Integration status</h1>
        <p className="portal-copy">The main assistant already runs without these services, but these integrations upgrade the experience.</p>

        <div className="setup-grid-portal">
          <div className="portal-panel">
            <h3>Dify</h3>
            <div className="setup-line">Configured: {setup?.dify_configured ? 'Yes' : 'No'}</div>
            <div className="setup-line">Use a Chatflow and keep the API on /chat-messages.</div>
          </div>
          <div className="portal-panel">
            <h3>ElevenLabs</h3>
            <div className="setup-line">Configured: {setup?.elevenlabs_configured ? 'Yes' : 'No'}</div>
            <div className="setup-line">Voice input/output stays optional but fully supported.</div>
          </div>
          <div className="portal-panel">
            <h3>Cognee</h3>
            <div className="setup-line">Enabled: {setup?.cognee_enabled ? 'Yes' : 'No'}</div>
            <div className="setup-line">Local memory still works even if Cognee is off.</div>
          </div>
          <div className="portal-panel">
            <h3>Local memory records</h3>
            <div className="setup-line">Count: {setup?.memory_count ?? 0}</div>
          </div>
        </div>

        <div className="portal-panel wide">
          <h3>Recommended integration settings</h3>
          <ul className="portal-list">
            <li><strong>Dify:</strong> Chatflow only. Keep the Start node without required custom inputs. Enable Memory in the LLM node.</li>
            <li><strong>ElevenLabs:</strong> Keep Speech-to-Text enabled and Text-to-Speech enabled on the same API key.</li>
            <li><strong>Cognee:</strong> Optional. No structural change is required because local memory now works by default.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
