from __future__ import annotations

from typing import Any, Dict, List
import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.memory_service import relevant_memory_context


def _normalize_base_url() -> str:
    if not settings.dify_api_url:
        return ''
    return settings.dify_api_url if settings.dify_api_url.endswith('/v1') else f"{settings.dify_api_url}/v1"



def _context_block(mode: str, context: List[Dict[str, Any]]) -> str:
    if not context:
        return f'Current assistant mode: {mode}. No cards were provided.'

    lines = [f'Current assistant mode: {mode}. Visible update cards:']
    for index, item in enumerate(context[:10], start=1):
        lines.append(
            f"{index}. [{item.get('type','item')}] {item.get('title','Untitled')} | "
            f"source={item.get('source','Unknown')} | urgency={item.get('urgency','?')} | "
            f"actions={', '.join(action.get('label','') for action in item.get('actions', [])[:3])}"
        )
    lines.append('Be practical. Reference the visible cards instead of inventing data.')
    return '\n'.join(lines)



def ask_dify(query: str, conversation_id: str | None = None, mode: str = 'assistant', context: List[Dict[str, Any]] | None = None):
    context = context or []
    memory_context = relevant_memory_context(query)
    grounded_query = f"{_context_block(mode, context)}\n\n{memory_context}\n\nUser request:\n{query}".strip()

    if not (_normalize_base_url() and settings.dify_api_key):
        top = context[:4]
        bullets = '\n'.join(f"- {item.get('title')}: {item.get('description')}" for item in top)
        memory_line = f"\n\n{memory_context}" if memory_context else ''
        answer = (
            'Dify is not configured yet, so here is a grounded local fallback based on the visible assistant updates:\n'
            f'{bullets or "- No visible cards available."}{memory_line}\n\n'
            'Start with the highest-urgency deadline, then use the built-in calendar, Gmail, or map actions directly from the assistant cards.'
        )
        return {
            'status': 'not_configured',
            'answer': answer,
            'conversation_id': conversation_id,
        }

    url = f"{_normalize_base_url()}/chat-messages"
    body: Dict[str, Any] = {
        'inputs': {},
        'query': grounded_query,
        'response_mode': 'blocking',
        'user': settings.dify_user_id,
    }
    if conversation_id:
        body['conversation_id'] = conversation_id

    headers = {
        'Authorization': f'Bearer {settings.dify_api_key}',
        'Content-Type': 'application/json',
    }

    try:
        response = httpx.post(url, headers=headers, json=body, timeout=90)
        response.raise_for_status()
        data = response.json()
        return {
            'status': 'success',
            'answer': data.get('answer', 'No answer returned.'),
            'conversation_id': data.get('conversation_id'),
            'message_id': data.get('message_id'),
        }
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=500, detail=f'Dify request failed: {exc}')
