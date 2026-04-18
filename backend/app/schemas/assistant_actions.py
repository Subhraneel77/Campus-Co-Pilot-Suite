from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ActionKind(str, Enum):
    OPEN_URL = "open_url"
    CALENDAR = "calendar"
    EMAIL = "email"
    MAP = "map"
    PAGE = "page"


class QuickAction(BaseModel):
    id: str
    kind: ActionKind
    label: str
    url: str
    description: Optional[str] = None
    source: Optional[str] = None
    priority: int = 50
    new_tab: bool = True
    icon: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    answer: str
    conversation_id: Optional[str] = None
    actions: List[QuickAction] = Field(default_factory=list)
    transcript: Optional[str] = None
    language_code: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_mime: Optional[str] = None