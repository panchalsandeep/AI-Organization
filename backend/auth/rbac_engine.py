from typing import List


class RBACEngine:
    """Simplified role-based access control engine."""

    def __init__(self, roles: dict[str, list[str]]):
        self.roles = roles

    def has_permission(self, role: str, permission: str) -> bool:
        permissions = self.roles.get(role, [])
        return permission in permissions

    def add_role(self, role: str, permissions: List[str]) -> None:
        self.roles[role] = permissions

    def remove_role(self, role: str) -> None:
        if role in self.roles:
            del self.roles[role]

    def list_roles(self) -> list[str]:
        return list(self.roles.keys())
