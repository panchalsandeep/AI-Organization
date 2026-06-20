import os
from openai import OpenAI
from backend.security.secrets_manager import SecretsManager

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio using OpenAI Whisper API.
    Provides mock/fallback text if API key or file is missing.
    """
    api_key = SecretsManager.get_openai_api_key()
    if not api_key or not os.path.exists(audio_file_path):
        return (
            "[Mock Transcript]: In this meeting, the leadership team discussed the transition to "
            "the Phase 2 operational intelligence platform. We decided that Sprint 1 database "
            "migrations and multi-tenant routing must be fully verified and covered by mocked unit tests. "
            "Sprint 2 will focus on WebSockets, real-time KPI engines, Whisper transcription, and "
            "threaded comments collaboration."
        )

    try:
        client = OpenAI(api_key=api_key)
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
    except Exception as e:
        return f"[Mock Fallback Transcript - API Error: {str(e)}]: Discussed architecture guidelines."
