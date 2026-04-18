from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException

from app.config import settings

STORE_PATH = Path(__file__).resolve().parents[2] / 'data' / 'memory_store.json'
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


DEFAULT_MEMORYS = [
    {
        'id': 'seed-1',
        'category': 'interest',
        'text': 'Interested in AI, robotics, and practical hackathon demos.',
        'source': 'seed',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'tags': ['ai', 'robotics', 'hackathon'],
    }
]


def _load() -> List[dict]:
    if not STORE_PATH.exists():
        _save(DEFAULT_MEMORYS)
    try:
        return json.loads(STORE_PATH.read_text(encoding='utf-8'))
    except Exception:
        _save(DEFAULT_MEMORYS)
        return list(DEFAULT_MEMORYS)



def _save(records: List[dict]):
    STORE_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')



def _slug(prefix: str, value: str) -> str:
    core = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:28] or 'item'
    return f'{prefix}-{core}-{int(datetime.now(timezone.utc).timestamp())}'



def _category_for_text(text: str) -> str:
    text_l = text.lower()
    if 'favourite subject' in text_l or 'favorite subject' in text_l:
        return 'favorite_subject'
    if 'interest' in text_l or 'interested in' in text_l:
        return 'interest'
    if 'prefer' in text_l or 'preference' in text_l:
        return 'preference'
    if 'remind' in text_l or 'reminder' in text_l:
        return 'reminder_preference'
    return 'general'



def _extract_tags(text: str) -> List[str]:
    words = re.findall(r'[A-Za-z][A-Za-z0-9\-]{2,}', text.lower())
    stop = {'that', 'this', 'with', 'from', 'your', 'have', 'will', 'what', 'when', 'where', 'subject', 'favorite', 'favourite'}
    tags = []
    for word in words:
        if word not in stop and word not in tags:
            tags.append(word)
        if len(tags) == 6:
            break
    return tags



def save_local_memory(text: str, source: str = 'manual') -> dict:
    records = _load()
    clean = text.strip()
    if not clean:
        raise HTTPException(status_code=400, detail='Memory text cannot be empty')
    record = {
        'id': _slug('mem', clean),
        'category': _category_for_text(clean),
        'text': clean,
        'source': source,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'tags': _extract_tags(clean),
    }
    records.insert(0, record)
    _save(records)
    _sync_to_cognee_if_enabled(clean)
    return record



def list_local_memories() -> List[dict]:
    return _load()



def search_local_memories(query: str, limit: int = 8) -> List[dict]:
    query_l = query.lower().strip()
    records = _load()
    if not query_l:
        return records[:limit]

    scored = []
    for record in records:
        hay = ' '.join([record.get('text', ''), ' '.join(record.get('tags', [])), record.get('category', '')]).lower()
        score = 0
        for token in query_l.split():
            if token in hay:
                score += 1
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get('created_at', '')), reverse=False)
    return [record for _, record in scored[:limit]]



def infer_memory_candidate(text: str) -> Optional[str]:
    clean = text.strip()
    lower = clean.lower()
    patterns = [
        'remember that',
        'my interests are',
        'i am interested in',
        "i'm interested in",
        'my favourite subject is',
        'my favorite subject is',
        'i prefer',
        'for future remember',
    ]
    if any(pattern in lower for pattern in patterns):
        return clean
    return None



def relevant_memory_context(query: str) -> str:
    lower = query.lower()
    if any(trigger in lower for trigger in ['what are my interests', 'what is my favourite subject', 'what is my favorite subject', 'what do you remember', 'what are my preferences']):
        items = search_local_memories(query, limit=5)
    else:
        items = search_local_memories(query, limit=3)
    if not items:
        return ''
    lines = ['Relevant stored memory:']
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. [{item.get('category','general')}] {item.get('text','')}")
    return '\n'.join(lines)



def memory_write(payload):
    record = save_local_memory(payload.text, source='manual')
    return {
        'status': 'success',
        'message': 'Memory saved successfully.',
        'record': record,
    }



def memory_search(payload):
    results = search_local_memories(payload.query)
    return {
        'status': 'success',
        'results': results,
    }



def memory_list():
    records = list_local_memories()
    return {
        'status': 'success',
        'count': len(records),
        'records': records,
    }



def _sync_to_cognee_if_enabled(text: str):
    if not settings.enable_cognee:
        return
    try:
        import cognee

        async def _run():
            await cognee.remember(text)

        asyncio.run(_run())
    except Exception:
        # Keep local memory reliable even if Cognee is not configured correctly.
        return
