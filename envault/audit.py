"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


AUDIT_LOG_FILENAME = ".envault_audit.log"


class AuditError(Exception):
    """Raised when an audit log operation fails."""
    pass


class AuditLog:
    """Records and retrieves audit entries for vault operations."""

    def __init__(self, project_dir: Path):
        self.log_path = project_dir / AUDIT_LOG_FILENAME

    def record(self, action: str, user: Optional[str] = None, details: Optional[str] = None) -> None:
        """Append a new audit entry to the log file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user": user or os.environ.get("USER", "unknown"),
            "details": details or "",
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            raise AuditError(f"Failed to write audit log: {e}") from e

    def read(self, limit: Optional[int] = None) -> List[dict]:
        """Return audit entries, most recent last. Optionally limit count."""
        if not self.log_path.exists():
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            entries = [json.loads(line) for line in lines]
            if limit is not None:
                entries = entries[-limit:]
            return entries
        except (OSError, json.JSONDecodeError) as e:
            raise AuditError(f"Failed to read audit log: {e}") from e

    def clear(self) -> None:
        """Remove all audit log entries."""
        try:
            if self.log_path.exists():
                self.log_path.unlink()
        except OSError as e:
            raise AuditError(f"Failed to clear audit log: {e}") from e
