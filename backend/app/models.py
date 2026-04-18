from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


DashboardMode = Literal['demo', 'live', 'assistant']
ActionKind = Literal['calendar', 'gmail', 'external', 'maps']
ItemType = Literal['deadline', 'event', 'career', 'campus', 'food', 'navigation', 'transport']


class DashboardQuery(BaseModel):
    mode: DashboardMode = 'assistant'
    campus_id: Optional[int] = None
    canteen_id: Optional[str] = None
    location_query: Optional[str] = None


class ItemAction(BaseModel):
    id: str
    label: str
    kind: ActionKind
    url: str


class DashboardItem(BaseModel):
    id: str
    type: ItemType
    title: str
    description: str
    source: str
    urgency: int = Field(ge=1, le=10)
    due_date: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    live: bool = False
    source_url: Optional[str] = None
    actions: List[ItemAction] = []


class DashboardResponse(BaseModel):
    mode: DashboardMode
    headline: str
    summary: str
    data_status: str
    items: List[DashboardItem]
    controls: Dict[str, Any]


class AgentRequest(BaseModel):
    message: str = Field(alias='query')
    conversation_id: Optional[str] = None
    mode: DashboardMode = 'assistant'
    context: List[Dict[str, Any]] = []
    voice_reply: bool = False

    class Config:
        populate_by_name = True


class MemoryWrite(BaseModel):
    text: str


class MemoryQuery(BaseModel):
    query: str
