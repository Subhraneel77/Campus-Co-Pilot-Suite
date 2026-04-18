import { useEffect, useState } from 'react'
import { listMemories, saveMemory, searchMemory } from '../api'

export function MemoryView() {
  const [records, setRecords] = useState([])
  const [query, setQuery] = useState('')
  const [note, setNote] = useState('My favourite subject is Deep Learning and I like structured morning reminders.')
  const [loading, setLoading] = useState(true)
  const [searchResults, setSearchResults] = useState([])
  const [message, setMessage] = useState('')

  async function load() {
    setLoading(true)
    try {
      const result = await listMemories()
      setRecords(result.records || [])
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleSave() {
    const result = await saveMemory(note)
    setMessage(result.message || 'Memory saved.')
    await load()
  }

  async function handleSearch() {
    const result = await searchMemory(query)
    setSearchResults(result.results || [])
  }

  return (
    <div className="portal-page">
      <div className="portal-card">
        <div className="eyebrow">Memory</div>
        <h1>Stored memory details</h1>
        <p className="portal-copy">This page shows what the assistant has stored locally. If Cognee is enabled, the same user fact can also be synced there.</p>

        <div className="portal-grid">
          <div className="portal-panel">
            <h3>Add memory</h3>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={4} />
            <button className="primary-button" onClick={handleSave}>Save memory</button>
          </div>

          <div className="portal-panel">
            <h3>Search memory</h3>
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search interests, favourite subject, preferences..." />
            <button className="secondary-button solid" onClick={handleSearch}>Search</button>
            {searchResults.length > 0 && (
              <div className="memory-result-list">
                {searchResults.map((record) => (
                  <div key={record.id} className="memory-record small">
                    <div className="memory-category">{record.category}</div>
                    <div>{record.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {message && <div className="toast portal-toast">{message}</div>}

        <div className="portal-panel wide">
          <h3>All stored memory</h3>
          {loading ? <div>Loading memory...</div> : records.length === 0 ? <div>No stored memory yet.</div> : (
            <div className="memory-record-list">
              {records.map((record) => (
                <article key={record.id} className="memory-record">
                  <div className="memory-record-top">
                    <span className="memory-category">{record.category}</span>
                    <span className="memory-date">{new Date(record.created_at).toLocaleString()}</span>
                  </div>
                  <div className="memory-text">{record.text}</div>
                  <div className="memory-tags">{(record.tags || []).map((tag) => <span key={tag}>#{tag}</span>)}</div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
