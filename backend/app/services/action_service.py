from datetime import datetime
from app.models import ActionRequest


def _timestamp():
    return datetime.now().strftime('%H:%M:%S')



def create_reminder(payload: ActionRequest):
    return {
        'status': 'success',
        'kind': 'reminder',
        'message': f'Reminder created for “{payload.title}” at {_timestamp()}.',
    }



def create_email_draft(payload: ActionRequest):
    draft = (
        f"Subject: Registration for {payload.title}\n\n"
        f"Hello,\n"
        f"I would like to register for {payload.title}.\n\n"
        f"Best regards,\n"
        f"Pranjaly"
    )
    return {
        'status': 'success',
        'kind': 'email-draft',
        'message': f'Email draft prepared for “{payload.title}” at {_timestamp()}.',
        'draft': draft,
    }



def create_team_message(payload: ActionRequest):
    return {
        'status': 'success',
        'kind': 'team-message',
        'message': f'Team message drafted for “{payload.title}” at {_timestamp()}.',
        'draft': f'Hi team, I want to start the work for {payload.title} today. Are you free to align on the first draft?',
    }
