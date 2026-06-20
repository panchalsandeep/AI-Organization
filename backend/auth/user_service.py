from typing import Optional


class User:
    def __init__(self, user_id: str, username: str, password: str, permissions: list[str]):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.permissions = permissions


# Placeholder user store. Replace with real user storage in database.
USER_STORE = {
    "admin": User(
        user_id="e10b5e63-1a96-4c2e-b72a-a182a0cc9c8f",
        username="admin",
        password="admin123",
        permissions=[
            "tenant:read",
            "tenant:write",
            "role:read",
            "role:write",
            "audit:read",
            "audit:write",
            "workflow:execute",
            "workflow:manage"
        ]
    )
}


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = USER_STORE.get(username)
    if user and user.password == password:
        return user
    return None
