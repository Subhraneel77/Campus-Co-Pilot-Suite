import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.schemas.assistant_actions import ActionKind, QuickAction
from app.services.action_links import (
    gmail_compose_link,
    google_calendar_link,
    google_maps_search_link,
    navigatum_search_link,
)


ROOM_KEYWORDS = {
    "room", "study room", "study-room", "empty room", "free room", "space", "study space"
}
TODO_KEYWORDS = {
    "to do", "todo", "to-do", "updates", "today", "urgent", "deadline", "tasks", "immediate"
}
WORKSHOP_KEYWORDS = {
    "workshop", "sign me up", "signup", "sign up", "register", "registration", "women in ai"
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_any(text: str, keywords: set[str]) -> bool:
    text_n = normalize(text)
    return any(k in text_n for k in keywords)


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", normalize(text)))


def flatten_catalog(payload: Any, inherited_source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Robustly flattens your existing unified home payload without depending on one fixed shape.
    Any dict with a title becomes a candidate item.
    """
    items: List[Dict[str, Any]] = []

    def walk(node: Any, source_hint: Optional[str] = None):
        if isinstance(node, list):
            for x in node:
                walk(x, source_hint)
            return

        if isinstance(node, dict):
            source = node.get("source") or source_hint

            if node.get("title"):
                items.append({
                    "id": node.get("id") or str(uuid4()),
                    "title": node.get("title", ""),
                    "description": node.get("description", ""),
                    "type": node.get("type") or node.get("kind") or "",
                    "urgency": int(node.get("urgency", 0) or 0),
                    "source": source,
                    "location": node.get("location", ""),
                    "url": node.get("url") or node.get("page_url") or node.get("link") or "",
                    "registration_url": node.get("registration_url", ""),
                    "contact_email": node.get("contact_email", ""),
                    "due_date": node.get("due_date", ""),
                    "meta": node,
                })

            for k, v in node.items():
                if isinstance(v, (list, dict)):
                    walk(v, source or k)

    walk(payload, inherited_source)
    return items


def extract_building_name(message: str) -> Optional[str]:
    text = normalize(message)

    patterns = [
        r"near the ([a-z0-9\s\-]+?) building",
        r"near ([a-z0-9\s\-]+?) building",
        r"near the ([a-z0-9\s\-]+?)(?: today| at |\?|,|$)",
        r"near ([a-z0-9\s\-]+?)(?: today| at |\?|,|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    known = ["math", "mathematics", "informatics", "physics", "garching", "mi"]
    for k in known:
        if k in text:
            return k

    return None


def extract_time_phrase(message: str) -> Optional[str]:
    text = normalize(message)

    patterns = [
        r"(today at \d{1,2}(?::\d{2})?\s?(?:am|pm)?)",
        r"(tomorrow at \d{1,2}(?::\d{2})?\s?(?:am|pm)?)",
        r"(at \d{1,2}(?::\d{2})?\s?(?:am|pm)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def best_workshop_match(message: str, catalog: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    text_tokens = tokenize(message)
    best_item = None
    best_score = 0

    for item in catalog:
        title = item.get("title", "")
        desc = item.get("description", "")
        combined = f"{title} {desc}"
        item_tokens = tokenize(combined)

        score = len(text_tokens.intersection(item_tokens))

        if "workshop" in normalize(combined):
            score += 2
        if "event" in normalize(item.get("type", "")):
            score += 1

        if score > best_score:
            best_score = score
            best_item = item

    return best_item if best_score >= 2 else None


def top_todo_items(catalog: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    ranked = sorted(
        [x for x in catalog if x.get("urgency", 0) > 0],
        key=lambda x: x.get("urgency", 0),
        reverse=True,
    )
    return ranked[:limit]


def resolve_actions(message: str, catalog: List[Dict[str, Any]]) -> List[QuickAction]:
    text = normalize(message)
    actions: List[QuickAction] = []

    wants_room = contains_any(text, ROOM_KEYWORDS)
    wants_todo = contains_any(text, TODO_KEYWORDS)
    wants_workshop = contains_any(text, WORKSHOP_KEYWORDS)

    # 1) Study room / location actions
    if wants_room:
        building = extract_building_name(message) or "TUM"
        time_phrase = extract_time_phrase(message)

        query = f"study room near {building}"
        if time_phrase:
            query = f"{query} {time_phrase}"

        actions.append(
            QuickAction(
                id=f"room-nav-{uuid4().hex[:8]}",
                kind=ActionKind.MAP,
                label=f"Find study rooms near {building.title()}",
                url=navigatum_search_link(query),
                description="Open NavigaTUM search for nearby rooms and spaces.",
                source="NavigaTUM",
                priority=95,
                icon="map-pin",
                meta={"query": query},
            )
        )

        actions.append(
            QuickAction(
                id=f"room-gmaps-{uuid4().hex[:8]}",
                kind=ActionKind.MAP,
                label=f"Open {building.title()} in Google Maps",
                url=google_maps_search_link(f"{building} building TUM"),
                description="Open the building area in Google Maps.",
                source="Google Maps",
                priority=80,
                icon="navigation",
                meta={"query": f"{building} building TUM"},
            )
        )

    # 2) To-do / urgent tasks actions
    if wants_todo:
        todo_items = top_todo_items(catalog, limit=3)

        for idx, item in enumerate(todo_items, start=1):
            title = item.get("title", "Task")
            desc = item.get("description", "")
            location = item.get("location", "")

            start_dt = datetime.now() + timedelta(hours=idx)
            end_dt = start_dt + timedelta(hours=1)

            actions.append(
                QuickAction(
                    id=f"todo-cal-{uuid4().hex[:8]}",
                    kind=ActionKind.CALENDAR,
                    label=f"Add to Google Calendar: {title}",
                    url=google_calendar_link(
                        title=title,
                        details=desc,
                        location=location,
                        start_dt=start_dt,
                        end_dt=end_dt,
                    ),
                    description="Create a quick calendar event for this urgent item.",
                    source=item.get("source") or "Campus Copilot",
                    priority=max(60, item.get("urgency", 0) * 10),
                    icon="calendar",
                    meta={"item_id": item.get("id")},
                )
            )

            # If a task looks collaborative or academic, prepare email shortcut too
            if any(k in normalize(title + " " + desc) for k in ["project", "proposal", "exercise", "assignment"]):
                actions.append(
                    QuickAction(
                        id=f"todo-mail-{uuid4().hex[:8]}",
                        kind=ActionKind.EMAIL,
                        label=f"Draft email about: {title}",
                        url=gmail_compose_link(
                            subject=f"Regarding {title}",
                            body=f"Hi,\n\nI am following up regarding: {title}.\n\nContext: {desc}\n\nBest regards,",
                        ),
                        description="Open Gmail with a prefilled draft.",
                        source="Gmail",
                        priority=max(50, item.get("urgency", 0) * 8),
                        icon="mail",
                        meta={"item_id": item.get("id")},
                    )
                )

    # 3) Workshop / sign-up actions
    if wants_workshop:
        workshop = best_workshop_match(message, catalog)

        if workshop:
            title = workshop.get("title", "Workshop")
            registration_url = workshop.get("registration_url") or workshop.get("url")
            contact_email = workshop.get("contact_email")
            desc = workshop.get("description", "")

            if registration_url:
                actions.append(
                    QuickAction(
                        id=f"workshop-page-{uuid4().hex[:8]}",
                        kind=ActionKind.PAGE,
                        label=f"Open workshop page: {title}",
                        url=registration_url,
                        description="Open the event or registration page.",
                        source=workshop.get("source") or "Workshop",
                        priority=92,
                        icon="external-link",
                        meta={"item_id": workshop.get("id")},
                    )
                )

            actions.append(
                QuickAction(
                    id=f"workshop-mail-{uuid4().hex[:8]}",
                    kind=ActionKind.EMAIL,
                    label=f"Draft sign-up email: {title}",
                    url=gmail_compose_link(
                        to=contact_email or "",
                        subject=f"Registration request for {title}",
                        body=(
                            f"Hello,\n\nI would like to register for {title}.\n\n"
                            f"Please let me know the next steps.\n\nThank you."
                        ),
                    ),
                    description="Open Gmail with a sign-up draft.",
                    source="Gmail",
                    priority=90,
                    icon="mail",
                    meta={"item_id": workshop.get("id")},
                )
            )
        else:
            # generic safe fallback if no workshop record matched
            actions.append(
                QuickAction(
                    id=f"workshop-mail-generic-{uuid4().hex[:8]}",
                    kind=ActionKind.EMAIL,
                    label="Draft workshop registration email",
                    url=gmail_compose_link(
                        subject="Workshop registration request",
                        body="Hello,\n\nI would like to register for the workshop.\n\nPlease let me know the next steps.\n\nThank you.",
                    ),
                    description="Open Gmail with a generic sign-up draft.",
                    source="Gmail",
                    priority=70,
                    icon="mail",
                    meta={"fallback": True},
                )
            )

    # Deduplicate by label + url
    deduped = []
    seen = set()
    for action in sorted(actions, key=lambda x: x.priority, reverse=True):
        key = (action.label, action.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(action)

    return deduped[:8]


def build_dify_context(message: str, actions: List[QuickAction]) -> str:
    if not actions:
        return (
            f"User request:\n{message}\n\n"
            "No quick actions were resolved. Give a short helpful answer and clearly say no direct quick actions are available."
        )

    action_lines = []
    for i, action in enumerate(actions, start=1):
        action_lines.append(
            f"{i}. {action.label} ({action.kind.value}) - {action.description or 'Quick action available'}"
        )

    return (
        f"User request:\n{message}\n\n"
        "Resolved quick actions already available in the app:\n"
        + "\n".join(action_lines)
        + "\n\nWrite a short assistant reply that:\n"
          "- summarizes what was prepared\n"
          "- tells the user to use the quick action buttons below\n"
          "- does not invent links or URLs\n"
          "- orders the response by usefulness\n"
    )