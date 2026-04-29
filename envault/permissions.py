"""Permission management for envault.

Handles access control for shared vaults, allowing team leads to
grant or revoke access to specific .env files for team members.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class PermissionError(Exception):
    """Raised when a permission operation fails."""
    pass


class PermissionManager:
    """Manages read/write permissions for vault access.

    Permissions are stored in a JSON file alongside the shared vault,
    keyed by member identifier (e.g. email or username).

    Example permissions file structure::

        {
            "members": {
                "alice@example.com": {
                    "role": "admin",
                    "granted_at": "2024-01-01T00:00:00+00:00",
                    "granted_by": "owner"
                },
                "bob@example.com": {
                    "role": "reader",
                    "granted_at": "2024-01-02T00:00:00+00:00",
                    "granted_by": "alice@example.com"
                }
            }
        }
    """

    ROLES = ("owner", "admin", "writer", "reader")
    PERMISSIONS_FILENAME = ".envault_permissions.json"

    def __init__(self, shared_dir: str) -> None:
        """Initialise the PermissionManager.

        Args:
            shared_dir: Path to the shared directory containing vault files.
        """
        self.shared_dir = Path(shared_dir)
        self.permissions_file = self.shared_dir / self.PERMISSIONS_FILENAME
        self._data: Dict = {"members": {}}

        if self.permissions_file.exists():
            self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load permissions from disk."""
        try:
            with open(self.permissions_file, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            raise PermissionError(f"Failed to load permissions file: {exc}") from exc

    def _save(self) -> None:
        """Persist permissions to disk."""
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.permissions_file, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
        except OSError as exc:
            raise PermissionError(f"Failed to save permissions file: {exc}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grant(self, member: str, role: str, granted_by: str) -> None:
        """Grant a role to a team member.

        Args:
            member: Identifier for the team member (e.g. email).
            role: One of 'owner', 'admin', 'writer', 'reader'.
            granted_by: Identifier of the person granting access.

        Raises:
            PermissionError: If the role is invalid.
        """
        if role not in self.ROLES:
            raise PermissionError(
                f"Invalid role '{role}'. Choose from: {', '.join(self.ROLES)}"
            )

        self._data["members"][member] = {
            "role": role,
            "granted_at": datetime.now(timezone.utc).isoformat(),
            "granted_by": granted_by,
        }
        self._save()

    def revoke(self, member: str) -> None:
        """Revoke all permissions for a team member.

        Args:
            member: Identifier for the team member to remove.

        Raises:
            PermissionError: If the member is not found.
        """
        if member not in self._data["members"]:
            raise PermissionError(f"Member '{member}' not found in permissions.")

        del self._data["members"][member]
        self._save()

    def get_role(self, member: str) -> Optional[str]:
        """Return the role assigned to a member, or None if not found.

        Args:
            member: Identifier for the team member.
        """
        entry = self._data["members"].get(member)
        return entry["role"] if entry else None

    def has_permission(self, member: str, required_role: str) -> bool:
        """Check whether a member holds at least the required role.

        Role hierarchy (highest to lowest): owner > admin > writer > reader.

        Args:
            member: Identifier for the team member.
            required_role: Minimum role needed.

        Returns:
            True if the member's role is equal to or higher than required_role.
        """
        if required_role not in self.ROLES:
            raise PermissionError(f"Unknown role: '{required_role}'")

        member_role = self.get_role(member)
        if member_role is None:
            return False

        return self.ROLES.index(member_role) <= self.ROLES.index(required_role)

    def list_members(self) -> List[Dict]:
        """Return a list of all members with their permission details.

        Returns:
            List of dicts, each containing 'member', 'role', 'granted_at',
            and 'granted_by' keys.
        """
        return [
            {"member": member, **details}
            for member, details in self._data["members"].items()
        ]
