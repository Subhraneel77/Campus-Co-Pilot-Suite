const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

async function parseJson(response) {
  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data
}

export async function fetchCopilotHome({ campusId, canteenId, locationQuery } = {}) {
  const params = new URLSearchParams()
  if (campusId) params.set('campus_id', String(campusId))
  if (canteenId) params.set('canteen_id', canteenId)
  if (locationQuery) params.set('location_query', locationQuery)
  const response = await fetch(`${API_URL}/api/copilot/home?${params.toString()}`)
  return parseJson(response)
}

export async function fetchSetupStatus() {
  const response = await fetch(`${API_URL}/api/setup-status`)
  return parseJson(response)
}

export function getBriefingVoiceUrl({ campusId, canteenId, locationQuery } = {}) {
  const params = new URLSearchParams()
  if (campusId) params.set('campus_id', String(campusId))
  if (canteenId) params.set('canteen_id', canteenId)
  if (locationQuery) params.set('location_query', locationQuery)
  return `${API_URL}/api/voice/briefing?${params.toString()}`
}

export async function textChat({ message, query, conversationId, voiceReply, context }) {
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  const response = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message || query,
      conversation_id: conversationId || null,
      voice_reply: voiceReply || false,
      context: context || [],
    }),
  });

  if (!response.ok) {
    let detail = "Chat failed";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch (_) { }
    throw new Error(detail);
  }

  return response.json();
}

export async function voiceChat({ audioFile, file, conversationId, context }) {
  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

  const formData = new FormData();
  formData.append("file", audioFile || file);

  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  if (context) {
    formData.append("context_json", JSON.stringify(context));
  }

  const response = await fetch(`${API_URL}/api/voice-chat`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = "Voice chat failed";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch (_) { }
    throw new Error(detail);
  }

  return response.json();
}

export async function saveMemory(text) {
  const response = await fetch(`${API_URL}/api/memory/remember`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return parseJson(response)
}

export async function searchMemory(query) {
  const response = await fetch(`${API_URL}/api/memory/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  return parseJson(response)
}

export async function listMemories() {
  const response = await fetch(`${API_URL}/api/memory/list`)
  return parseJson(response)
}
