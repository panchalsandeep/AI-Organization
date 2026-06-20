import os
from typing import Optional
from backend.config.settings import OPENAI_API_KEY


class SecretsManager:
    @staticmethod
    def get_secret(name: str) -> Optional[str]:
        return os.getenv(name)

    @staticmethod
    def set_secret(name: str, value: str) -> None:
        # For now, persist in environment only
        os.environ[name] = value

    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        return SecretsManager.get_secret("OPENAI_API_KEY")
