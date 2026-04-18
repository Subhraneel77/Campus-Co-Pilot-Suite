from datetime import datetime, timedelta


def iso(dt: datetime):
    return dt.strftime('%Y-%m-%dT%H:%M:%S')


def get_demo_items():
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    week_later = now + timedelta(days=7)
    two_days = now + timedelta(days=2)
    tomorrow = now + timedelta(days=1)

    ml_item = {
        'id': 'grade-ml',
        'type': 'event',
        'title': 'Machine Learning – Grade received: 1.3',
        'description': 'Your exam results for Machine Learning have just been published in TUMonline. Congratulations on the strong performance.',
        'source': 'TUMonline Integration',
        'urgency': 9,
        'due_date': iso(now),
        'location': None,
        'status': 'New notification',
        'live': False,
        'actions': [
            {
                'id': 'external',
                'label': 'Open TUMonline to view details',
                'kind': 'external',
                'url': 'https://campus.tum.de/',
            }
        ],
    }

    ds_item = {
        'id': 'urgent-ds',
        'type': 'deadline',
        'title': 'Data Science Survival Skills – Urgent Attention Required',
        'description': 'You have 12 hours left to complete the final peer-review assignment. Please prioritize this immediately.',
        'source': 'Moodle Integration',
        'urgency': 10,
        'due_date': iso(now + timedelta(hours=12)),
        'location': None,
        'status': 'Actionable now',
        'live': False,
        'actions': [
            {
                'id': 'calendar',
                'label': 'Block next 2 hours in Calendar',
                'kind': 'calendar',
                'title': 'Data Science peer-review',
                'details': 'Final peer-review assignment for Data Science Survival Skills.',
                'start': iso(now + timedelta(minutes=15)),
                'end': iso(now + timedelta(hours=2, minutes=15)),
            },
            {
                'id': 'external',
                'label': 'Open Assignment on Moodle',
                'kind': 'external',
                'url': 'https://moodle.tum.de/',
            }
        ],
    }

    base_items = [
        {
            'id': 'dl-ex3',
            'type': 'deadline',
            'title': 'Deep Learning – Exercise 3 submission is due this week',
            'description': 'The worksheet and notebook still need polishing. Prioritize a 90-minute study block tonight and submit before the weekly rush.',
            'source': 'Mock Moodle / authentic demo',
            'urgency': 10,
            'due_date': iso(two_days),
            'location': None,
            'status': 'Actionable now',
            'live': False,
            'actions': [
                {
                    'id': 'calendar',
                    'label': 'Add submission block to Google Calendar',
                    'kind': 'calendar',
                    'title': 'Deep Learning Exercise 3 – focused submission block',
                    'details': 'Finish Exercise 3, verify notebook output, and submit before the deadline.',
                    'start': iso(now + timedelta(hours=3)),
                    'end': iso(now + timedelta(hours=4, minutes=30)),
                },
                {
                    'id': 'email',
                    'label': 'Open Gmail draft to teammates',
                    'kind': 'gmail',
                    'to': '',
                    'subject': 'Deep Learning Exercise 3 – quick sync today?',
                    'body': 'Hi team,%0D%0A%0D%0AI am planning to finish Exercise 3 today. Shall we do a quick sync before submission?%0D%0A%0D%0ABest,%0D%0APranjaly',
                },
            ],
        },
        {
            'id': 'air-proposal',
            'type': 'deadline',
            'title': 'AI in Robotics – proposal milestone next week',
            'description': 'The proposal is not due immediately, but the strongest teams typically lock scope, hardware assumptions, and datasets at least a week early.',
            'source': 'Mock TUMonline / authentic demo',
            'urgency': 8,
            'due_date': iso(week_later),
            'location': 'Project workspace',
            'status': 'Needs coordination',
            'live': False,
            'actions': [
                {
                    'id': 'calendar',
                    'label': 'Book a proposal sprint',
                    'kind': 'calendar',
                    'title': 'AI in Robotics – proposal sprint',
                    'details': 'Outline objective, dataset assumptions, robot stack, and first milestone plan.',
                    'start': iso(tomorrow.replace(hour=18)),
                    'end': iso(tomorrow.replace(hour=19, minute=30)),
                },
                {
                    'id': 'email',
                    'label': 'Open Gmail draft to teammates',
                    'kind': 'gmail',
                    'to': '',
                    'subject': 'AI in Robotics proposal – can we align this week?',
                    'body': 'Hi,%0D%0A%0D%0AI would like to align on the AI in Robotics proposal this week so that we can fix the scope early.%0D%0A%0D%0ABest,%0D%0APranjaly',
                },
            ],
        },
        {
            'id': 'women-ai',
            'type': 'event',
            'title': 'Women in AI workshop tomorrow at 14:00',
            'description': 'High-signal networking and internship visibility opportunity. Great fit if you want to build an AI profile beyond coursework.',
            'source': 'Mock university announcement / authentic demo',
            'urgency': 7,
            'due_date': iso(tomorrow.replace(hour=14)),
            'location': 'Audimax',
            'status': 'Opportunity',
            'live': False,
            'actions': [
                {
                    'id': 'calendar',
                    'label': 'Add workshop to Google Calendar',
                    'kind': 'calendar',
                    'title': 'Women in AI workshop',
                    'details': 'Workshop attendance reminder.',
                    'location': 'Audimax',
                    'start': iso(tomorrow.replace(hour=14)),
                    'end': iso(tomorrow.replace(hour=16)),
                },
                {
                    'id': 'email',
                    'label': 'Open Gmail registration draft',
                    'kind': 'gmail',
                    'to': '',
                    'subject': 'Registration for Women in AI workshop',
                    'body': 'Hello,%0D%0A%0D%0AI would like to register for the Women in AI workshop.%0D%0A%0D%0ABest regards,%0D%0APranjaly',
                },
            ],
        },
        {
            'id': 'career-ml',
            'type': 'career',
            'title': 'Two ML-flavoured student roles match your profile',
            'description': 'Treat these as secondary after academic urgencies. Both are strong for a portfolio if you want to strengthen applied ML experience.',
            'source': 'Mock career portal / authentic demo',
            'urgency': 5,
            'due_date': None,
            'location': None,
            'status': 'Worth reviewing',
            'live': False,
            'actions': [
                {
                    'id': 'calendar',
                    'label': 'Block time to review roles',
                    'kind': 'calendar',
                    'title': 'Review ML student roles',
                    'details': 'Review role fit and shortlist applications.',
                    'start': iso((now + timedelta(days=1)).replace(hour=20)),
                    'end': iso((now + timedelta(days=1)).replace(hour=20, minute=45)),
                },
                {
                    'id': 'external',
                    'label': 'Open LinkedIn jobs',
                    'kind': 'external',
                    'url': 'https://www.linkedin.com/jobs/',
                },
            ],
        },
    ]

    return [ml_item, ds_item] + base_items


def get_demo_controls():
    return {
        'campus_options': [],
        'canteen_options': [
            {'label': 'Mensa Garching', 'value': 'mensa-garching'},
            {'label': 'Mensa Arcisstrasse', 'value': 'mensa-arcisstrasse'},
            {'label': 'StuBistro Grosshadern', 'value': 'stubistro-grosshadern'},
        ],
        'selected_campus_id': None,
        'selected_canteen_id': 'mensa-garching',
        'selected_location_query': 'garching',
    }
