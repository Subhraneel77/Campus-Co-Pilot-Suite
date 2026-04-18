import json
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import AgentRequest, MemoryQuery, MemoryWrite
from app.services.copilot_service import build_copilot_home
from app.services.dashboard_service import get_dashboard
from app.services.memory_service import memory_list, memory_search, memory_write
from app.services.voice_service import assistant_text_chat, assistant_voice_chat, create_briefing_voice

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok', 'app': settings.app_name}


@app.get('/api/dashboard')
def dashboard(mode: str = 'demo', campus_id: Optional[int] = None, canteen_id: Optional[str] = None, location_query: Optional[str] = None):
    return get_dashboard(mode=mode, campus_id=campus_id, canteen_id=canteen_id, location_query=location_query)


@app.get('/api/copilot/home')
def copilot_home(campus_id: Optional[int] = None, canteen_id: Optional[str] = None, location_query: Optional[str] = None):
    return build_copilot_home(campus_id=campus_id, canteen_id=canteen_id, location_query=location_query)


@app.get('/api/setup-status')
def setup_status():
    memories = memory_list()
    return {
        'dify_configured': bool(settings.dify_api_url and settings.dify_api_key),
        'elevenlabs_configured': bool(settings.elevenlabs_api_key and settings.elevenlabs_voice_id),
        'cognee_enabled': settings.enable_cognee,
        'default_campus_id': settings.default_campus_id,
        'default_canteen_id': settings.default_canteen_id,
        'default_location_query': settings.default_location_query,
        'memory_count': memories.get('count', 0),
    }


@app.get('/api/voice/briefing')
def voice_briefing(campus_id: Optional[int] = None, canteen_id: Optional[str] = None, location_query: Optional[str] = None):
    return create_briefing_voice(campus_id=campus_id, canteen_id=canteen_id, location_query=location_query)


@app.post('/api/chat')
def assistant_chat(payload: AgentRequest):
    return assistant_text_chat(
        message=payload.message,
        conversation_id=payload.conversation_id,
        mode=payload.mode,
        context=payload.context,
        voice_reply=payload.voice_reply,
    )


@app.post('/api/voice-chat')
async def assistant_voice(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    mode: str = Form('assistant'),
    context_json: Optional[str] = Form(None),
):
    # Read the file content into bytes as expected by the updated service
    file_bytes = await file.read()
    
    # Parse context from JSON if provided
    context = []
    if context_json:
        try:
            context = json.loads(context_json)
        except Exception:
            pass

    return assistant_voice_chat(
        file_bytes=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        conversation_id=conversation_id,
        mode=mode,
        context=context,
    )


@app.post('/api/memory/remember')
def remember(payload: MemoryWrite):
    return memory_write(payload)


@app.post('/api/memory/search')
def search_memory(payload: MemoryQuery):
    return memory_search(payload)


@app.get('/api/memory/list')
def list_memories():
    return memory_list()
