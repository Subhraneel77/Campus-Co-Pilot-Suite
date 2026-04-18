from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, quote_plus


def google_calendar_link(
    title: str,
    details: str = "",
    location: str = "",
    start_dt: Optional[datetime] = None,
    end_dt: Optional[datetime] = None,
) -> str:
    if start_dt is None:
        start_dt = datetime.now() + timedelta(hours=1)
    if end_dt is None:
        end_dt = start_dt + timedelta(hours=1)

    dates = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": details,
        "location": location,
        "dates": dates,
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params, quote_via=quote_plus)}"


def gmail_compose_link(
    subject: str,
    body: str = "",
    to: str = "",
    cc: str = "",
) -> str:
    params = {
        "view": "cm",
        "fs": "1",
        "su": subject,
        "body": body,
    }
    if to:
        params["to"] = to
    if cc:
        params["cc"] = cc
    return f"https://mail.google.com/mail/?{urlencode(params, quote_via=quote_plus)}"


def google_maps_search_link(query: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def navigatum_search_link(query: str) -> str:
    return f"https://nav.tum.de/search?query={quote_plus(query)}"