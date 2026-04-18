import { useEffect, useMemo, useRef, useState } from 'react'
import { textChat, voiceChat } from '../api'

const STORAGE_KEY = 'campus-copilot-unified-assistant-v1'
const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']

function pickSupportedMimeType() {
  if (!window.MediaRecorder) return ''
  for (const type of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return ''
}

function playAudioReply(audioBase64, audioMime = 'audio/mpeg') {
  if (!audioBase64) return Promise.resolve()
  const audio = new Audio(`data:${audioMime};base64,${audioBase64}`)
  return audio.play()
}
function openAction(url) {
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

function QuickActions({ actions = [] }) {
  if (!actions.length) return null

  return (
    <div className="assistant-quick-actions">
      {actions.map((action) => (
        <button
          key={action.id}
          className={`assistant-quick-btn kind-${action.kind}`}
          onClick={() => openAction(action.url)}
          title={action.label}
        >
          <span className="assistant-quick-label">{action.label}</span>
        </button>
      ))}
    </div>
  )
}
function ActionCard({ item, onAction }) {
  const urgency = item.urgency || 0;
  const redAlpha = (urgency / 10) * 0.15; // Dynamic red intensity based on urgency

  return (
    <article
      className={`update-card ${item.live ? 'live' : 'demo'}`}
      style={{
        background: `linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(220, 38, 38, ${redAlpha}))`,
        borderColor: `rgba(220, 38, 38, ${redAlpha * 2})`
      }}
    >
      <div className="update-card-top">
        <span className={`chip chip-${item.type}`}>{item.type}</span>
        <span className={`urgency-badge ${item.urgency >= 8 ? 'danger' : item.urgency >= 6 ? 'warning' : 'calm'}`}>
          Urgency {item.urgency}/10
        </span>
      </div>
      <h4>{item.title}</h4>
      <p>{item.description}</p>
      <div className="update-meta">
        <span><strong>Source:</strong> {item.source}</span>
        {item.location ? <span><strong>Location:</strong> {item.location}</span> : null}
        {item.due_date ? <span><strong>When:</strong> {item.due_date.replace('T', ' ')}</span> : null}
      </div>
      <div className="update-actions">
        {(item.actions || []).slice(0, 2).map((action) => (
          <button key={action.id} className="mini-action" onClick={() => onAction(item, action)}>{action.label}</button>
        ))}
      </div>
    </article>
  )
}

export function UnifiedAssistantPanel({ home, onAction, onToast, onRefresh }) {
  const [interactionMode, setInteractionMode] = useState('write')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState('')
  const [enableVoiceReply, setEnableVoiceReply] = useState(false)
  const [isBusy, setIsBusy] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [status, setStatus] = useState('Ready')
  const [error, setError] = useState('')

  const [autopilotMode, setAutopilotMode] = useState(false)
  const [autopilotQueue, setAutopilotQueue] = useState([])

  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const messageEndRef = useRef(null)

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
      if (saved.messages) setMessages(saved.messages)
      if (saved.conversationId) setConversationId(saved.conversationId)
      if (saved.enableVoiceReply) setEnableVoiceReply(saved.enableVoiceReply)
    } catch (_) { }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ messages, conversationId, enableVoiceReply }))
  }, [messages, conversationId, enableVoiceReply])

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const groupedSections = home?.sections || []
  const immediateItems = home?.immediate_items || []
  const allContext = home?.all_items || []

  const introText = useMemo(() => {
    if (!home) return ''
    return `${home.summary}\n\nCurrent Updates are shown below with direct actions for Google Calendar, Gmail, Maps, or public campus tools.`
  }, [home])

  function openPrompt(prompt) {
    setInput(prompt)
  }

  function clearConversation() {
    setMessages([])
    setConversationId('')
    setInput('')
    setStatus('New conversation')
    setError('')
    localStorage.removeItem(STORAGE_KEY)
  }

  function startAutopilot() {
    if (!window.confirm("Are you allowing full permissions for the Autonomous Agent to manage calendars, emails, and logistical requests?")) return;
    setAutopilotMode(true);
    if (immediateItems.length > 0) {
      setAutopilotQueue([...immediateItems]);
    } else {
      onToast?.("No current updates to process right now.");
      setAutopilotMode(false);
    }
  }

  function stopAutopilot() {
    setAutopilotMode(false);
    setAutopilotQueue([]);
    onToast?.("Returned to Manual Mode.");
  }

  function handleAutopilotAccept(item) {
    (item.actions || []).forEach(action => {
      openAction(action.url);
    });
    advanceAutopilot();
  }

  function advanceAutopilot() {
    setAutopilotQueue(prev => {
      const nextQ = prev.slice(1);
      if (nextQ.length === 0) {
        setAutopilotMode(false);
        onToast?.("Autopilot sequence complete. All tasks managed autonomously.");
      }
      return nextQ;
    });
  }

  const activeAutopilotItem = autopilotMode && autopilotQueue.length > 0 ? autopilotQueue[0] : null;

  async function sendTextMessage(overrideText = null) {
    const query = (overrideText ?? input).trim()
    if (!query || isBusy) return
    setError('')
    setIsBusy(true)
    setStatus('Thinking...')
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', text: query, mode: 'write' }])
    setInput('')
    try {
      const result = await textChat({ message: query, conversationId, context: allContext, voiceReply: enableVoiceReply })

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          text: result.answer,
          mode: 'write',
          actions: result.actions || [],
        },
      ])
      setConversationId(result.conversation_id || '')
      setStatus('Reply ready')
      if (result.audio_base64) await playAudioReply(result.audio_base64, result.audio_mime)
    } catch (err) {
      setError(err.message || 'Assistant request failed')
      setStatus('Error')
      onToast?.(err.message || 'Assistant request failed')
    } finally {
      setIsBusy(false)
    }
  }

  async function startRecording() {
    setError('')
    setStatus('Requesting microphone...')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []
      const mimeType = pickSupportedMimeType()
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      recorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = async () => {
        const finalMimeType = recorder.mimeType || 'audio/webm'
        const extension = finalMimeType.includes('ogg') ? 'ogg' : finalMimeType.includes('mp4') ? 'mp4' : 'webm'
        const blob = new Blob(chunksRef.current, { type: finalMimeType })
        const file = new File([blob], `voice-message.${extension}`, { type: finalMimeType })
        await sendVoiceMessage(file)
        if (streamRef.current) streamRef.current.getTracks().forEach((track) => track.stop())
      }
      recorder.start()
      setIsRecording(true)
      setStatus('Listening...')
    } catch (_) {
      setError('Microphone access was denied or unavailable.')
      setStatus('Microphone unavailable')
    }
  }

  function stopRecording() {
    if (!recorderRef.current) return
    setIsRecording(false)
    setStatus('Uploading audio...')
    recorderRef.current.stop()
  }

  async function sendVoiceMessage(audioFile) {
    setIsBusy(true)
    try {
      const result = await voiceChat({ audioFile, conversationId, context: allContext })
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'user',
          text: result.transcript || '(voice message)',
          mode: 'speak',
        },
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          text: result.answer,
          mode: 'speak',
          actions: result.actions || [],
        },
      ])
      setConversationId(result.conversation_id || '')
      setStatus('Playing reply...')
      if (result.audio_base64) await playAudioReply(result.audio_base64, result.audio_mime)
      setStatus('Reply ready')
    } catch (err) {
      setError(err.message || 'Voice chat failed')
      setStatus('Error')
      onToast?.(err.message || 'Voice chat failed')
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <section className="assistant-one-channel">
    {activeAutopilotItem && (
      <div className="autopilot-overlay">
        <div className="autopilot-modal">
          <h3 className="autopilot-head">🤖 Autonomous Execution Sequence</h3>
          <div className="autopilot-body">
            {activeAutopilotItem.id === 'grade-ml' ? (
              <p>Hey, yesterday your Machine Learning grades came, it's quite good. You scored 1.3 german grade. Congratulations buddy. Keep it up.</p>
            ) : activeAutopilotItem.id === 'urgent-ds' ? (
              <p>I noticed you have a Data Science deadline in 12 hours. I have proactively drafted an email to your project partner and pre-reserved a 2-hour blocking slot in your calendar. Should I execute these now?</p>
            ) : (
              <p>I proactively identified: "{activeAutopilotItem.title}". I have prepared the relevant actions. Should I execute them?</p>
            )}
          </div>
          <div className="autopilot-actions">
            <button className="autopilot-btn accept" onClick={() => handleAutopilotAccept(activeAutopilotItem)}>ACCEPT</button>
            <button className="autopilot-btn deny" onClick={advanceAutopilot}>DENY</button>
          </div>
        </div>
      </div>
    )}
    <div className="assistant-hero">
      <div>
        <div className="eyebrow">🌟 Master Hub</div>
        <h2>{home?.headline || 'Welcome to Campus Co-Pilot Suite 👋'}</h2>
        <p>{introText}</p>
      </div>
      <div className="assistant-hero-actions" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
        <div className="mode-toggle-group">
          <button className={`clear-btn ${!autopilotMode ? 'active' : ''}`} onClick={stopAutopilot} style={{ fontWeight: !autopilotMode ? 'bold' : 'normal' }}>🖐️ Manual Mode</button>
          <button className={`clear-btn ${autopilotMode ? 'active' : ''}`} onClick={startAutopilot} style={{ fontWeight: autopilotMode ? 'bold' : 'normal' }}>🤖 Autopilot Mode</button>
        </div>
        <button className="clear-btn" onClick={clearConversation}>New chat</button>
      </div>
    </div>

    <div className="quick-strip">
      <div className="quick-stat"><strong>{home?.stats?.urgent ?? 0}</strong><span>urgent actions</span></div>
      <div className="quick-stat"><strong>{home?.stats?.demo ?? 0}</strong><span>Study cards</span></div>
      <div className="quick-stat"><strong>{home?.stats?.live ?? 0}</strong><span>live campus cards</span></div>
      <div className="quick-stat"><strong>{home?.stats?.total ?? 0}</strong><span>total updates</span></div>
    </div>

    <h3 style={{ margin: '24px 0 8px 18px', fontSize: '1.2rem', color: '#334155' }}>Frequently asked questions</h3>
    <div className="prompt-row">
      {(home?.quick_prompts || []).map((prompt) => (
        <button key={prompt} className="prompt-pill" onClick={() => openPrompt(prompt)}>{prompt}</button>
      ))}
    </div>

    <div className="assistant-layout-grid">
      <div className="assistant-feed-card">
        <div className="assistant-meta-row">
          <div className="mode-switch compact">
            <button className={interactionMode === 'write' ? 'active' : ''} onClick={() => setInteractionMode('write')}>✍️ Write</button>
            <button className={interactionMode === 'speak' ? 'active' : ''} onClick={() => setInteractionMode('speak')}>🎙️ Speak</button>
          </div>
          <div className="assistant-status-line">
            <span className={`assistant-status ${isRecording ? 'live' : ''}`}>{status}</span>
            <label className="voice-reply-toggle">
              <input type="checkbox" checked={enableVoiceReply} onChange={(e) => setEnableVoiceReply(e.target.checked)} />
              Voice reply for typed messages
            </label>
          </div>
        </div>

        {error && <div className="assistant-error">{error}</div>}

        <div className="chat-shell unified">
          <div className="chat-messages">
            <div className="chat-bubble assistant intro-bubble">
              <div className="bubble-role">Campus Copilot · overview</div>
              <div className="bubble-text">{introText}</div>
            </div>

            <div className="embedded-sections">
              <div className="embedded-group">
                <div className="embedded-head">Current Updates</div>
                <div className="embedded-grid">
                  {immediateItems.map((item) => <ActionCard key={item.id} item={item} onAction={onAction} />)}
                </div>
              </div>

              {groupedSections.map((section) => (
                <div className="embedded-group" key={section.id}>
                  <div className="embedded-head">{section.label}</div>
                  <p className="embedded-copy">{section.description}</p>
                  <div className="embedded-grid">
                    {section.items.map((item) => <ActionCard key={item.id} item={item} onAction={onAction} />)}
                  </div>
                </div>
              ))}
            </div>

            {messages.map((msg) => (
              <div key={msg.id} className={`chat-bubble ${msg.role === 'assistant' ? 'assistant' : 'user'}`}>
                <div className="bubble-role">{msg.role === 'assistant' ? 'Campus Copilot' : 'You'} · {msg.mode}</div>
                <div className="bubble-text">{msg.text}</div>

                {msg.role === 'assistant' && msg.actions?.length > 0 ? (
                  <QuickActions actions={msg.actions} />
                ) : null}
              </div>
            ))}
            <div ref={messageEndRef} />
          </div>

          {interactionMode === 'write' ? (
            <div className="chat-composer unified-composer">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    sendTextMessage()
                  }
                }}
                placeholder="Ask for today's updates, request only urgent tasks, ask where to go next, or tell the assistant something to remember..."
                rows={4}
                disabled={isBusy}
              />
              <button className="send-btn" onClick={() => sendTextMessage()} disabled={isBusy}>{isBusy ? 'Sending...' : 'Send message'}</button>
            </div>
          ) : (
            <div className="voice-composer unified-composer">
              {!isRecording ? (
                <button className="voice-btn" onClick={startRecording} disabled={isBusy}>{isBusy ? 'Processing...' : 'Start speaking'}</button>
              ) : (
                <button className="voice-btn stop" onClick={stopRecording}>Stop and send</button>
              )}
              <div className="voice-hint">Speak in your preferred language. The assistant will transcribe your speech, combine demo study + live campus context, then reply with actions and voice if configured.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  </section>
  )
}
