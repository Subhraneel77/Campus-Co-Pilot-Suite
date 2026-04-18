from __future__ import annotations

from datetime import datetime, timedelta
from urllib.parse import quote, urlencode
import httpx

from app.config import settings
from app.sample_data import get_demo_controls, get_demo_items


CANTEEN_OPTIONS = [
    {'label': 'Mensa Garching', 'value': 'mensa-garching'},
    {'label': 'Mensa Arcisstrasse', 'value': 'mensa-arcisstrasse'},
    {'label': 'Mensa Leopoldstrasse', 'value': 'mensa-leopoldstrasse'},
]


def _calendar_url(title: str, start_iso: str, end_iso: str, details: str = '', location: str = '') -> str:
    def normalize(value: str) -> str:
        return datetime.fromisoformat(value).strftime('%Y%m%dT%H%M%S')

    params = {
        'action': 'TEMPLATE',
        'text': title,
        'details': details,
        'location': location,
        'dates': f"{normalize(start_iso)}/{normalize(end_iso)}",
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"


def _gmail_url(subject: str, body: str, to: str = '') -> str:
    params = {
        'view': 'cm',
        'fs': '1',
        'su': subject,
        'body': body,
        'to': to,
    }
    return f"https://mail.google.com/mail/?{urlencode(params)}"


def _maps_url(target: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote(target)}"


def _navigatum_url(query: str) -> str:
    return f"https://nav.tum.de/search?query={quote(query)}"


def _week_url(canteen_id: str) -> str:
    today = datetime.now().date()
    year, week, _ = today.isocalendar()
    return f"https://tum-dev.github.io/eat-api/{canteen_id}/{year}/{week}.json"


def _http_get_json(url: str):
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        response = client.get(url, headers={'User-Agent': 'CampusCopilot/1.0'})
        response.raise_for_status()
        return response.json()


def _normalize_actions(items):
    normalized = []
    for item in items:
        item = dict(item)
        actions = []
        for action in item.get('actions', []):
            action = dict(action)
            if action['kind'] == 'calendar':
                action['url'] = _calendar_url(
                    title=action.get('title', item['title']),
                    start_iso=action['start'],
                    end_iso=action['end'],
                    details=action.get('details', item['description']),
                    location=action.get('location', item.get('location') or ''),
                )
            elif action['kind'] == 'gmail':
                action['url'] = _gmail_url(
                    subject=action.get('subject', item['title']),
                    body=action.get('body', item['description']),
                    to=action.get('to', ''),
                )
            actions.append({
                'id': action['id'],
                'label': action['label'],
                'kind': action['kind'],
                'url': action['url'],
            })
        item['actions'] = actions
        normalized.append(item)
    return normalized


def get_demo_dashboard():
    items = _normalize_actions(get_demo_items())
    urgent = sum(1 for item in items if item['urgency'] >= 8)
    summary = (
        f"You currently have {urgent} high-priority academic tasks pending. "
        "This environment simulates authentic academic planning, enabling proactive study management."
    )
    return {
        'mode': 'demo',
        'headline': 'Demo academic operations',
        'summary': summary,
        'data_status': 'Curated mock data for login-free demos',
        'items': items,
        'controls': get_demo_controls(),
    }


def _build_live_items(campus_id: int | None, canteen_id: str, location_query: str):
    live_items = []
    statuses = []
    controls = {
        'campus_options': [],
        'canteen_options': CANTEEN_OPTIONS,
        'selected_campus_id': campus_id,
        'selected_canteen_id': canteen_id,
        'selected_location_query': location_query,
    }

    try:
        campuses = _http_get_json('https://api.srv.nat.tum.de/api/rom/campus')
        controls['campus_options'] = [
            {'label': campus.get('name', f"Campus {campus.get('id')}"), 'value': campus.get('id')}
            for campus in campuses[:8]
        ]
        statuses.append('NAT campus API live')
        if campus_id is None and campuses:
            campus_id = campuses[0].get('id')
            controls['selected_campus_id'] = campus_id
    except Exception:
        campuses = []
        statuses.append('NAT campus API fallback')

    if campus_id is not None:
        try:
            buildings = _http_get_json(f'https://api.srv.nat.tum.de/api/rom/building?campus_id={campus_id}')
            preview = buildings[:4]
            codes = ', '.join([b.get('building_code', '?') for b in preview]) or 'No codes returned'
            live_items.append({
                'id': f'live-building-{campus_id}',
                'type': 'campus',
                'title': 'Public TUM room and building data is reachable',
                'description': f"Campus {campus_id} returned {len(buildings)} building record(s). Preview codes: {codes}.",
                'source': 'TUM NAT Rooms API',
                'urgency': 7,
                'due_date': None,
                'location': f'Campus {campus_id}',
                'status': 'Live public data',
                'live': True,
                'source_url': 'https://api.srv.nat.tum.de/public',
                'actions': [
                    {
                        'id': 'external',
                        'label': 'Open NAT API docs',
                        'kind': 'external',
                        'url': 'https://api.srv.nat.tum.de/public',
                    },
                    {
                        'id': 'maps',
                        'label': 'Open campus on Google Maps',
                        'kind': 'maps',
                        'url': _maps_url(f'TUM campus {campus_id} Munich'),
                    },
                ],
            })
            statuses.append('NAT building API live')
        except Exception:
            live_items.append({
                'id': 'live-building-fallback',
                'type': 'campus',
                'title': 'Room and building lookup is prepared for public TUM APIs',
                'description': 'The app is configured for NAT room data, but this run used a graceful fallback so your demo does not break on network issues.',
                'source': 'TUM NAT Rooms API',
                'urgency': 5,
                'due_date': None,
                'location': None,
                'status': 'Fallback',
                'live': True,
                'source_url': 'https://api.srv.nat.tum.de/public',
                'actions': [
                    {
                        'id': 'external',
                        'label': 'Open NAT API docs',
                        'kind': 'external',
                        'url': 'https://api.srv.nat.tum.de/public',
                    }
                ],
            })
            statuses.append('NAT building API fallback')

    try:
        location = _http_get_json(f'https://nav.tum.de/api/get/{quote(location_query)}?lang=en')
        location_name = location.get('name', location_query)
        parents = location.get('parent_names', [])
        description = f"{location_name} is available in NavigaTUM. Parent chain: {' → '.join(parents[:3]) or 'TUM campus hierarchy'}"
        coords = location.get('coords') or {}
        target = location_name
        if coords.get('lat') and coords.get('lon'):
            target = f"{coords['lat']},{coords['lon']}"
        live_items.append({
            'id': f'live-nav-{location_query}',
            'type': 'navigation',
            'title': f'Campus navigation is live for “{location_query}”',
            'description': description,
            'source': 'NavigaTUM',
            'urgency': 8,
            'due_date': None,
            'location': location_name,
            'status': 'Live public data',
            'live': True,
            'source_url': 'https://nav.tum.de/',
            'actions': [
                {
                    'id': 'external',
                    'label': 'Open in NavigaTUM',
                    'kind': 'external',
                    'url': _navigatum_url(location_query),
                },
                {
                    'id': 'maps',
                    'label': 'Open in Google Maps',
                    'kind': 'maps',
                    'url': _maps_url(target),
                },
            ],
        })
        statuses.append('NavigaTUM live')
    except Exception:
        live_items.append({
            'id': f'live-nav-fallback-{location_query}',
            'type': 'navigation',
            'title': f'Campus navigation shortcut ready for “{location_query}”',
            'description': 'The public location API did not answer in time, so the app falls back to a direct NavigaTUM search link.',
            'source': 'NavigaTUM',
            'urgency': 6,
            'due_date': None,
            'location': location_query,
            'status': 'Fallback',
            'live': True,
            'source_url': 'https://nav.tum.de/',
            'actions': [
                {
                    'id': 'external',
                    'label': 'Search in NavigaTUM',
                    'kind': 'external',
                    'url': _navigatum_url(location_query),
                }
            ],
        })
        statuses.append('NavigaTUM fallback')

    try:
        menu = _http_get_json(_week_url(canteen_id))
        today = datetime.now().strftime('%Y-%m-%d')
        days = menu.get('days', [])
        target_day = next((day for day in days if day.get('date') == today), days[0] if days else None)
        dishes = (target_day or {}).get('dishes', [])[:3]
        dish_names = '; '.join(d.get('name', 'Dish') for d in dishes) or 'Menu currently unavailable'
        lunch_start = datetime.now().replace(hour=12, minute=30, second=0, microsecond=0)
        live_items.append({
            'id': f'live-food-{canteen_id}',
            'type': 'food',
            'title': 'Today’s Mensa shortlist is live',
            'description': dish_names,
            'source': 'TUM-Dev Eat API',
            'urgency': 6,
            'due_date': target_day.get('date') if target_day else None,
            'location': canteen_id.replace('-', ' ').title(),
            'status': 'Live public data',
            'live': True,
            'source_url': 'https://tum-dev.github.io/eat-api/',
            'actions': [
                {
                    'id': 'calendar',
                    'label': 'Add lunch reminder',
                    'kind': 'calendar',
                    'url': _calendar_url(
                        title='Lunch break at Mensa',
                        start_iso=lunch_start.isoformat(),
                        end_iso=(lunch_start + timedelta(minutes=45)).isoformat(),
                        details=f"Check today’s menu at {canteen_id}.",
                        location=canteen_id.replace('-', ' ').title(),
                    ),
                },
                {
                    'id': 'external',
                    'label': 'Open full menu',
                    'kind': 'external',
                    'url': _week_url(canteen_id),
                },
            ],
        })
        statuses.append('Eat API live')
    except Exception:
        live_items.append({
            'id': f'live-food-fallback-{canteen_id}',
            'type': 'food',
            'title': 'Mensa helper ready',
            'description': 'The live menu endpoint was not available for this run, so the app keeps a direct API link as a reliable backup.',
            'source': 'TUM-Dev Eat API',
            'urgency': 4,
            'due_date': None,
            'location': canteen_id.replace('-', ' ').title(),
            'status': 'Fallback',
            'live': True,
            'source_url': 'https://tum-dev.github.io/eat-api/',
            'actions': [
                {
                    'id': 'external',
                    'label': 'Open menu endpoint',
                    'kind': 'external',
                    'url': _week_url(canteen_id),
                }
            ],
        })
        statuses.append('Eat API fallback')

    live_items.sort(key=lambda item: item['urgency'], reverse=True)
    return live_items, '; '.join(statuses), controls


def get_live_dashboard(campus_id: int | None, canteen_id: str | None, location_query: str | None):
    campus_id = campus_id if campus_id is not None else settings.default_campus_id
    canteen_id = canteen_id or settings.default_canteen_id
    location_query = location_query or settings.default_location_query

    items, status, controls = _build_live_items(campus_id, canteen_id, location_query)
    summary = (
        'The Live Campus module integrates publicly available TUM ecosystem endpoints to deliver real-time data. '
        'It seamlessly fuses your academic planning with dynamic logistical utilities, ensuring an uninterrupted administrative workflow.'
    )
    return {
        'mode': 'live',
        'headline': 'Live campus utilities',
        'summary': summary,
        'data_status': status,
        'items': items,
        'controls': controls,
    }


def get_dashboard(mode: str = 'demo', campus_id=None, canteen_id=None, location_query=None):
    if mode == 'live':
        return get_live_dashboard(campus_id, canteen_id, location_query)
    return get_demo_dashboard()
