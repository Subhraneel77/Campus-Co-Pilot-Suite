import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _split_origins(raw: str):
    values = [item.strip() for item in raw.split(',') if item.strip()]
    return values or ['*']


@dataclass
class Settings:
    app_name: str = os.getenv('APP_NAME', 'Campus Copilot')
    frontend_url: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    allowed_origins: list = None

    dify_api_url: str = os.getenv('DIFY_API_URL', '').rstrip('/')
    dify_api_key: str = os.getenv('DIFY_API_KEY', '')
    dify_user_id: str = os.getenv('DIFY_USER_ID', 'campus-copilot-local')

    elevenlabs_api_key: str = os.getenv('ELEVENLABS_API_KEY', '')
    elevenlabs_voice_id: str = os.getenv('ELEVENLABS_VOICE_ID', '')
    elevenlabs_tts_model: str = os.getenv('ELEVENLABS_TTS_MODEL', 'eleven_multilingual_v2')

    enable_cognee: bool = os.getenv('ENABLE_COGNEE', 'false').lower() == 'true'
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    cogwit_api_key: str = os.getenv('COGWIT_API_KEY', '')

    default_campus_id: int = int(os.getenv('DEFAULT_CAMPUS_ID', '1'))
    default_canteen_id: str = os.getenv('DEFAULT_CANTEEN_ID', 'mensa-garching')
    default_location_query: str = os.getenv('DEFAULT_LOCATION_QUERY', 'garching')

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = _split_origins(
                os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
            )


settings = Settings()
