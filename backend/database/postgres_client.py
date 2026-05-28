import psycopg
from backend.config.settings import DATABASE_URL

_conn = None

def get_connection():
    global _conn
    if _conn is None:
        _conn = psycopg.connect(DATABASE_URL)
    return _conn