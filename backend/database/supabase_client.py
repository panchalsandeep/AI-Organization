from supabase import create_client
from backend.config.settings import (
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

_supabase_client = None


def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_SERVICE_ROLE_KEY
        )
    return _supabase_client