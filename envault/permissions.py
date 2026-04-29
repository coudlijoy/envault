import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class PermissionError(Exception):
    pass


class PermissionManager:
    ROLES = {"admin", "editor", "viewer"}
    ROLE_CAPABILITIES = {
        "admin": {"read", "write", "lock", "unlock", "manage_users"},
        "editor": {"read", "write", "lock", "unlock"},
        "viewer": {"read"},
    }

    def __init__(self, permissions_path: Path):
        self.permissions_path = permissions_path
        self._permissions: Dict[str, str] = {}
        if permissions_path.exists():
            self._load()

    def _load(self):
        try:
            with open(self.permissions_path, "r") as f:
                self._permissions = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise PermissionError(f"Failed to load permissions: {e}")

    def _save(self):
        try:
            with open(self.permissions_path, "w") as f:
                json.dump(self._permissions, f, indent=2)
        except OSError as e:
            raise PermissionError(f"Failed to save permissions: {e}")

    def add_user(self, user: str, role: str):
        if role not in self.ROLES:
            raise PermissionError(f"Invalid role '{role}'. Must be one of: {', '.join(self.ROLES)}")
        self._permissions[user] = role
        self._save()

    def remove_user(self, user: str):
        if user not in self._permissions:
            raise PermissionError(f"User '{user}' not found in permissions")
        del self._permissions[user]
        self._save()

    def get_role(self, user: str) -> Optional[str]:
        return self._permissions.get(user)

    def can(self, user: str, capability: str) -> bool:
        role = self.get_role(user)
        if role is None:
            return False
        return capability in self.ROLE_CAPABILITIES.get(role, set())

    def list_users(self) -> List[Dict[str, str]]:
        return [{"user": u, "role": r} for u, r in self._permissions.items()]

    def require(self, user: str, capability: str):
        if not self.can(user, capability):
            role = self.get_role(user)
            if role is None:
                raise PermissionError(f"User '{user}' has no permissions")
            raise PermissionError(
                f"User '{user}' with role '{role}' cannot perform '{capability}'"
            )
