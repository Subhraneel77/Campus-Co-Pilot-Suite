from __future__ import annotations

import base64
from io import BytesIO
import json
import re
from typing import Optional
from urllib.parse import quote_plus

import httpx
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.copilot_service import build_copilot_home
from app.services.dify_service import ask_dify
from app.services.memory_service import infer_memory_candidate, save_local_memory

from app.schemas.assistant_actions import AssistantResponse
from app.services.action_resolver import (
    build_dify_context,
    flatten_catalog,
    resolve_actions,
)

def create_briefing_voice(campus_id=None, canteen_id=None, location_query=None):
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise HTTPException(status_code=400, detail='ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID is missing in backend/.env')

    home = build_copilot_home(campus_id=campus_id, canteen_id=canteen_id, location_query=location_query)
    top_titles = ', '.join(item['title'] for item in home['immediate_items'][:3])
    text = f"{home['headline']}. {home['summary']} Top immediate items: {top_titles}."
    audio_bytes = _tts_bytes(text)
    return StreamingResponse(BytesIO(audio_bytes), media_type='audio/mpeg')



def _tts_bytes(text: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}?output_format=mp3_44100_128"
    headers = {
        'xi-api-key': settings.elevenlabs_api_key,
        'Content-Type': 'application/json',
    }
    payload = {
        'text': text,
        'model_id': settings.elevenlabs_tts_model,
    }
    response = httpx.post(url, headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    return response.content



def _maybe_store_memory(message: str, source: str):
    candidate = infer_memory_candidate(message)
    if candidate:
        try:
            save_local_memory(candidate, source=source)
        except Exception:
            return

def _build_calendar_url(title: str, details: str = '', location: str = '') -> str:
    t = str(title or '')
    d = str(details or '')
    l = str(location or '')
    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote_plus(t)}"
        f"&details={quote_plus(d)}"
        f"&location={quote_plus(l)}"
    )


def _build_gmail_url(subject: str, body: str = '', to: str = '') -> str:
    s = str(subject or '')
    b = str(body or '')
    t = str(to or '')
    base = "https://mail.google.com/mail/?view=cm&fs=1"
    if t:
        base += f"&to={quote_plus(t)}"
    base += f"&su={quote_plus(s)}&body={quote_plus(b)}"
    return base


def _build_maps_url(query: str) -> str:
    q = str(query or '')
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(q)}"


def _build_navigatum_url(query: str) -> str:
    q = str(query or '')
    return f"https://nav.tum.de/search?query={quote_plus(q)}"


def _extract_building_query(message: str) -> Optional[str]:
    text = message.lower()

    patterns = [
        r"near the ([a-z0-9\s\-]+?) building",
        r"near ([a-z0-9\s\-]+?) building",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    if "math building" in text:
        return "math building"
    if "informatics" in text:
        return "informatics building"
    if "physics" in text:
        return "physics building"

    return None


def _resolve_assistant_actions(message: str, context: list) -> list:
    text = message.lower()
    actions = []

    # ---------------------------
    # 1) Study room / room search
    # ---------------------------
    if any(keyword in text for keyword in ['study room', 'empty room', 'free room', 'room near', 'study space']):
        building = _extract_building_query(message) or 'TUM'
        actions.append({
            'id': f'room-nav-{quote_plus(building)}',
            'label': f'Find study rooms near {building.title()}',
            'kind': 'maps',
            'url': _build_navigatum_url(f'{building} study room'),
        })
        actions.append({
            'id': f'room-gmaps-{quote_plus(building)}',
            'label': f'Open {building.title()} in Google Maps',
            'kind': 'maps',
            'url': _build_maps_url(f'{building} TUM'),
        })

    # ---------------------------
    # 2) To-do / urgent items
    # ---------------------------
    if any(keyword in text for keyword in ['to do', 'todo', 'to-do', 'today', 'updates', 'urgent', 'tasks']):
        sorted_items = sorted(context or [], key=lambda x: x.get('urgency', 0), reverse=True)
        top_items = sorted_items[:3]

        for item in top_items:
            title = item.get('title') or 'Task'
            description = item.get('description') or ''
            location = item.get('location') or ''

            actions.append({
                'id': f"calendar-{item.get('id', title)}",
                'label': f'Add to Google Calendar: {title}',
                'kind': 'calendar',
                'url': _build_calendar_url(title, description, location),
            })

            item_text = f"{title} {description}".lower()
            if any(k in item_text for k in ['project', 'proposal', 'exercise', 'assignment', 'workshop']):
                actions.append({
                    'id': f"gmail-{item.get('id', title)}",
                    'label': f'Draft email about: {title}',
                    'kind': 'gmail',
                    'url': _build_gmail_url(
                        subject=f"Regarding {title}",
                        body=f"Hello,\n\nI am following up regarding {title}.\n\nBest regards,"
                    ),
                })

    # ---------------------------
    # 3) Workshop / sign up
    # ---------------------------
    if any(keyword in text for keyword in ['workshop', 'sign me up', 'sign up', 'register', 'registration']):
        workshop_candidates = []
        for item in context or []:
            combined = f"{item.get('title', '')} {item.get('description', '')}".lower()
            if 'workshop' in combined or 'women in ai' in combined or item.get('type') == 'event':
                workshop_candidates.append(item)

        if workshop_candidates:
            best = workshop_candidates[0]

            # use item's existing actions if any
            for action in best.get('actions', [])[:2]:
                actions.append({
                    'id': f"existing-{action.get('id', '')}",
                    'label': action.get('label', 'Open workshop'),
                    'kind': action.get('kind', 'external'),
                    'url': action.get('url', ''),
                })

            actions.append({
                'id': f"gmail-workshop-{best.get('id', 'event')}",
                'label': f"Draft sign-up email: {best.get('title', 'Workshop')}",
                'kind': 'gmail',
                'url': _build_gmail_url(
                    subject=f"Registration request for {best.get('title', 'Workshop')}",
                    body=f"Hello,\n\nI would like to register for {best.get('title', 'this workshop')}.\n\nPlease let me know the next steps.\n\nThank you."
                ),
            })
        else:
            actions.append({
                'id': 'gmail-generic-workshop',
                'label': 'Draft workshop registration email',
                'kind': 'gmail',
                'url': _build_gmail_url(
                    subject='Workshop registration request',
                    body='Hello,\n\nI would like to register for the workshop.\n\nPlease let me know the next steps.\n\nThank you.'
                ),
            })

    # remove duplicate URLs
    deduped = []
    seen = set()
    for action in actions:
        key = (action.get('label'), action.get('url'))
        if key in seen:
            continue
        if not action.get('url'):
            continue
        seen.add(key)
        deduped.append(action)

    return deduped[:8]

def assistant_text_chat(message: str, conversation_id: Optional[str], mode: str, context: list, voice_reply: bool = False):
    _maybe_store_memory(message, source='assistant-text')

    # Resolve real quick actions based on current prompt + campus data
    actions = _resolve_assistant_actions(message, context or [])

    # Enrich Dify query with awareness of prepared actions
    dify_query = (
        f"User request:\n{message}\n\n"
        f"Quick actions already prepared in the app: {[action['label'] for action in actions]}\n\n"
        "Write a short helpful reply. "
        "Do not invent links. "
        "Summarize the quick actions if they exist and tell the user to use the buttons below."
    )

    result = ask_dify(query=dify_query, conversation_id=conversation_id, mode=mode, context=context)
    
    # Attach actions to result
    result['actions'] = actions

    if voice_reply and settings.elevenlabs_api_key and settings.elevenlabs_voice_id:
        audio_bytes = _tts_bytes(result['answer'])
        result['audio_base64'] = base64.b64encode(audio_bytes).decode('utf-8')
        result['audio_mime'] = 'audio/mpeg'
        
    return result



def assistant_voice_chat(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    conversation_id: Optional[str],
    mode: str,
    context: list,
):
    # 1) basic validation
    if not file_bytes:
        raise ValueError('Uploaded audio file is empty')

    if not settings.elevenlabs_api_key:
        raise ValueError('ELEVENLABS_API_KEY is missing')

    # 2) speech-to-text with ElevenLabs
    files = {
        'file': (
            filename or 'voice-message.webm',
            BytesIO(file_bytes),
            content_type or 'audio/webm',
        )
    }

    data = {
        'model_id': 'scribe_v2',
        # language_code intentionally omitted so ElevenLabs auto-detects
    }

    stt_response = requests.post(
        'https://api.elevenlabs.io/v1/speech-to-text',
        headers={'xi-api-key': settings.elevenlabs_api_key},
        files=files,
        data=data,
        timeout=90,
    )

    if stt_response.status_code >= 400:
        raise ValueError(f'ElevenLabs STT failed: {stt_response.status_code} {stt_response.text}')

    stt_payload = stt_response.json()
    transcript = (stt_payload.get('text') or '').strip()

    if not transcript:
        raise ValueError('ElevenLabs STT returned empty transcript')

    # 3) optionally store memory from the spoken request
    _maybe_store_memory(transcript, source='assistant-voice')

    # 4) resolve real quick actions from the spoken request + existing context
    actions = _resolve_assistant_actions(transcript, context or [])

    # 5) give Dify the spoken request + the already-prepared actions
    dify_query = (
        f"User request:\n{transcript}\n\n"
        f"Quick actions already prepared in the app: {[action['label'] for action in actions]}\n\n"
        "Write a short helpful reply. "
        "Do not invent links. "
        "If quick actions exist, tell the user to use the buttons below."
    )

    result = ask_dify(
        query=dify_query,
        conversation_id=conversation_id,
        mode=mode,
        context=context,
    )

    # 6) attach the quick actions so frontend can render clickable buttons
    result['actions'] = actions

    # 7) add transcript info
    result['transcript'] = transcript
    result['language_code'] = stt_payload.get('language_code')

    # 8) text-to-speech for the assistant reply
    if settings.elevenlabs_voice_id:
        reply_audio = _tts_bytes(result['answer'])
        result['audio_base64'] = base64.b64encode(reply_audio).decode('utf-8')
        result['audio_mime'] = 'audio/mpeg'

    return result