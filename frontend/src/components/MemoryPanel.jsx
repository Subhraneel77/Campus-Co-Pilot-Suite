import { useState } from 'react'

export function MemoryPanel({ onSave, onSearch }) {
  const [note, setNote] = useState('I prefer morning reminders, AI/robotics opportunities, and Garching as my default live campus focus.')
  const [query, setQuery] = useState('What does the app remember about my interests?')
  const [results, setResults] = useState([])
  const [saving, setSaving] = useState(false)
  const [searching, setSearching] = useState(false)

  async function save() {
    setSaving(true)
    await onSave(note)
    setSaving(false)
  }

  async function search() {
    setSearching(true)
    const found = await onSearch(query)
    setResults(found)
    setSearching(false)
  }

  return (
    <div className="stack">
      <div className="section-head">
        <div>
          <div className="eyebrow">Memory</div>
          <h2>Personal context and preferences</h2>
        </div>
        <div className="muted-badge">Cognee-ready</div>
      </div>

      <div className="assistant-form">
        <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={4} placeholder="Save a preference or long-term context..." />
        <button className="primary-button" type="button" onClick={save}>{saving ? 'Saving...' : 'Save memory'}</button>
      </div>

      <div className="assistant-form compact-gap">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search your saved memory..." />
        <button className="secondary-button solid" type="button" onClick={search}>{searching ? 'Searching...' : 'Search memory'}</button>
      </div>

      <div className="answer-card">
        <div className="meta-label">Memory results</div>
        {results.length ? (
          <ul className="result-list">
            {results.map((item, index) => <li key={index}>{item}</li>)}
          </ul>
        ) : (
          <div className="answer-copy">No results yet. If Cognee is not enabled, the backend returns a precise setup message instead of faking memory.</div>
        )}
      </div>
    </div>
  )
}
