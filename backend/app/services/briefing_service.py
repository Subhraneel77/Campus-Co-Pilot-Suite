from app.config import settings
from app.sample_data import get_demo_items


def get_ranked_items():
    items = sorted(get_demo_items(), key=lambda item: item['urgency'], reverse=True)
    return items



def get_briefing_payload():
    items = get_ranked_items()
    urgent = sum(1 for item in items if item['urgency'] >= 8)
    opportunities = sum(1 for item in items if item['type'] in ['event', 'career'])
    summary = (
        f'You have {urgent} urgent academic item(s) and {opportunities} opportunity item(s) today. '
        'Start with the graded assignment, then decide whether to register for the workshop.'
    )
    return {
        'greeting': 'Good morning, Pranjaly ✨',
        'summary': summary,
        'items': items,
    }



def get_setup_status():
    return {
        'demo_mode': settings.demo_mode,
        'dify_configured': bool(settings.dify_api_url and settings.dify_api_key),
        'elevenlabs_configured': bool(settings.elevenlabs_api_key),
        'cognee_enabled': settings.enable_cognee,
    }
