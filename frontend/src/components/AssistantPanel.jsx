import { useEffect, useRef, useState } from "react";
import { textChat, voiceChat } from "../api";

const STORAGE_KEY = "campus-copilot-chat-actions-v1";

const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4",
];

function pickSupportedMimeType() {
  if (!window.MediaRecorder) return "";
  for (const type of MIME_CANDIDATES) {
    if (MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return "";
}

function playAudioReply(audioBase64, audioMime = "audio/mpeg") {
  if (!audioBase64) return Promise.resolve();
  const audioSrc = `data:${audioMime};base64,${audioBase64}`;
  const audio = new Audio(audioSrc);
  return audio.play();
}

function openAction(action) {
  if (!action?.url) return;
  window.open(action.url, "_blank", "noopener,noreferrer");
}

function ActionButtons({ actions = [] }) {
  if (!actions.length) return null;

  return (
    <div className="action-grid">
      {actions.map((action) => (
        <button
          key={action.id}
          className={`quick-action kind-${action.kind}`}
          onClick={() => openAction(action)}
          title={action.description || action.label}
        >
          <div className="quick-action-label">{action.label}</div>
          {action.description ? (
            <div className="quick-action-desc">{action.description}</div>
          ) : null}
        </button>
      ))}
    </div>
  );
}

export default function AssistantPanel() {
  const [mode, setMode] = useState("write");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [enableVoiceReply, setEnableVoiceReply] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");

  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const messageEndRef = useRef(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      if (saved.messages) setMessages(saved.messages);
      if (saved.conversationId) setConversationId(saved.conversationId);
      if (typeof saved.enableVoiceReply === "boolean") {
        setEnableVoiceReply(saved.enableVoiceReply);
      }
    } catch (_) { }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        messages,
        conversationId,
        enableVoiceReply,
      })
    );
  }, [messages, conversationId, enableVoiceReply]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function clearConversation() {
    setMessages([]);
    setConversationId("");
    setInput("");
    setError("");
    setStatus("New conversation");
    localStorage.removeItem(STORAGE_KEY);
  }

  async function sendTextMessage() {
    const message = input.trim();
    if (!message || isBusy) return;

    setError("");
    setIsBusy(true);
    setStatus("Thinking...");

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: message,
      mode: "write",
      actions: [],
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const result = await textChat({ message, conversationId, voiceReply: enableVoiceReply });

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.answer,
        mode: "write",
        actions: result.actions || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(result.conversation_id || "");
      setStatus("Reply ready");

      if (result.audio_base64) {
        await playAudioReply(result.audio_base64, result.audio_mime);
      }
    } catch (err) {
      setError(err.message || "Chat failed");
      setStatus("Error");
    } finally {
      setIsBusy(false);
    }
  }

  async function startRecording() {
    setError("");
    setStatus("Requesting microphone...");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];

      const mimeType = pickSupportedMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Recording failed.");
        setIsRecording(false);
        setStatus("Error");
      };

      recorder.onstop = async () => {
        const finalMimeType = recorder.mimeType || "audio/webm";

        let extension = "webm";
        if (finalMimeType.includes("ogg")) extension = "ogg";
        if (finalMimeType.includes("mp4")) extension = "mp4";

        const blob = new Blob(chunksRef.current, { type: finalMimeType });
        const file = new File([blob], `voice-message.${extension}`, {
          type: finalMimeType,
        });

        await sendVoiceMessage(file);
        stopMicrophoneTracks();
      };

      recorder.start();
      setIsRecording(true);
      setStatus("Listening...");
    } catch (_) {
      setError("Microphone access was denied or unavailable.");
      setStatus("Microphone unavailable");
    }
  }

  function stopMicrophoneTracks() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }

  function stopRecording() {
    if (!recorderRef.current) return;
    setIsRecording(false);
    setStatus("Uploading audio...");
    recorderRef.current.stop();
  }

  async function sendVoiceMessage(audioFile) {
    setError("");
    setIsBusy(true);
    setStatus("Transcribing...");

    try {
      const result = await voiceChat({ audioFile, conversationId });

      const userMessage = {
        id: crypto.randomUUID(),
        role: "user",
        text: result.transcript || "(voice message)",
        mode: "speak",
        actions: [],
      };

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.answer,
        mode: "speak",
        actions: result.actions || [],
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setConversationId(result.conversation_id || "");
      setStatus("Playing reply...");

      await playAudioReply(result.audio_base64, result.audio_mime);
      setStatus("Reply ready");
    } catch (err) {
      setError(err.message || "Voice chat failed.");
      setStatus("Error");
    } finally {
      setIsBusy(false);
    }
  }

  function onInputKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendTextMessage();
    }
  }

  return (
    <section className="assistant-panel">
      <div className="assistant-topbar">
        <div>
          <h2>Campus Copilot Assistant</h2>
          <p>Type or speak. Quick actions appear directly under the assistant reply.</p>
        </div>
        <button className="clear-btn" onClick={clearConversation}>
          New chat
        </button>
      </div>

      <div className="mode-switch">
        <button
          className={mode === "write" ? "active" : ""}
          onClick={() => setMode("write")}
        >
          ✍️ Write
        </button>
        <button
          className={mode === "speak" ? "active" : ""}
          onClick={() => setMode("speak")}
        >
          🎙️ Speak
        </button>
      </div>

      <div className="assistant-meta">
        <span className={`assistant-status ${isRecording ? "live" : ""}`}>
          {status}
        </span>

        <label className="voice-reply-toggle">
          <input
            type="checkbox"
            checked={enableVoiceReply}
            onChange={(e) => setEnableVoiceReply(e.target.checked)}
          />
          Voice reply for typed messages
        </label>
      </div>

      {error && <div className="assistant-error">{error}</div>}

      <div className="chat-shell">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-empty">
              Ask for updates, study rooms, deadlines, routes, or workshop sign-up help.
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-bubble ${msg.role === "assistant" ? "assistant" : "user"}`}
              >
                <div className="bubble-role">
                  {msg.role === "assistant" ? "Campus Copilot" : "You"} · {msg.mode}
                </div>

                <div className="bubble-text">{msg.text}</div>

                {msg.role === "assistant" && msg.actions?.length > 0 ? (
                  <ActionButtons actions={msg.actions} />
                ) : null}
              </div>
            ))
          )}
          <div ref={messageEndRef} />
        </div>

        {mode === "write" ? (
          <div className="chat-composer">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder="Ask for updates, routes, rooms, workshops, deadlines..."
              rows={3}
              disabled={isBusy}
            />
            <button className="send-btn" onClick={sendTextMessage} disabled={isBusy}>
              {isBusy ? "Sending..." : "Send"}
            </button>
          </div>
        ) : (
          <div className="voice-composer">
            {!isRecording ? (
              <button className="voice-btn" onClick={startRecording} disabled={isBusy}>
                {isBusy ? "Processing..." : "Start speaking"}
              </button>
            ) : (
              <button className="voice-btn stop" onClick={stopRecording}>
                Stop and send
              </button>
            )}

            <div className="voice-hint">
              Speak naturally. The assistant will respond with quick actions when available.
            </div>
          </div>
        )}
      </div>
    </section>
  );
}