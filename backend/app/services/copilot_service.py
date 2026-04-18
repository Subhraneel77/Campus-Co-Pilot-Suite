from __future__ import annotations

from typing import Any, Dict, List

from app.services.dashboard_service import get_demo_dashboard, get_live_dashboard


def build_copilot_home(campus_id=None, canteen_id=None, location_query=None):
    demo = get_demo_dashboard()
    live = get_live_dashboard(campus_id, canteen_id, location_query)

    demo_items = demo.get('items', [])
    live_items = live.get('items', [])
    merged_items = sorted(demo_items + live_items, key=lambda item: item.get('urgency', 0), reverse=True)

    urgent_count = sum(1 for item in merged_items if item.get('urgency', 0) >= 8)
    immediate = merged_items[:5]

    headline = 'Welcome to Campus Co-Pilot Suite 👋'
    summary = (
        f'Good morning! ☀️ You currently have {urgent_count} urgent update(s) spanning your study schedule and live campus utilities. '
        'Leverage this unified workspace to seamlessly review your core priorities, draft essential emails 📧, instantiate Google Calendar events 📅, or intuitively navigate maps and campus tools 🗺️.'
    )

    quick_prompts = [
        'Good morning, what are today\'s updates?',
        'Show me only the urgent actions first.',
        'Which item should I handle before lunch?',
        'Summarise the live campus utilities for me.',
    ]

    return {
        'headline': headline,
        'summary': summary,
        'stats': {
            'urgent': urgent_count,
            'demo': len(demo_items),
            'live': len(live_items),
            'total': len(merged_items),
        },
        'immediate_items': immediate,
        'sections': [
            {
                'id': 'demo',
                'label': 'Study Updates',
                'description': demo.get('summary'),
                'items': demo_items,
            },
            {
                'id': 'live',
                'label': 'Live campus utilities',
                'description': live.get('summary'),
                'items': live_items,
            },
        ],
        'all_items': merged_items,
        'setup_status_hint': 'Assistant-first mode active. Memory and setup are available through the side dock.',
        'quick_prompts': quick_prompts,
        'controls': {
            'selected_campus_id': live['controls'].get('selected_campus_id'),
            'selected_canteen_id': live['controls'].get('selected_canteen_id'),
            'selected_location_query': live['controls'].get('selected_location_query'),
            'campus_options': live['controls'].get('campus_options', []),
            'canteen_options': live['controls'].get('canteen_options', []),
        },
    }
