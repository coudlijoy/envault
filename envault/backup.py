"""Backup and restore functionality for encrypted vault files."""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""
    pass


class BackupManager:
    """Manages versioned backups of vault files."""

    BACKUP_DIR_NAME = ".envault_backups"
    MAX_BACKUPS = 10

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.backup_dir = self.project_dir / self.BACKUP_DIR_NAME
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.backup_dir / "index.json"

    def _load_index(self) -> list:
        if not self._index_path.exists():
            return []
        with open(self._index_path, "r") as f:
            return json.load(f)

    def _save_index(self, index: list) -> None:
        with open(self._index_path, "w") as f:
            json.dump(index, f, indent=2)

    def create_backup(self, vault_path: str, label: str = "") -> str:
        """Create a timestamped backup of the given vault file."""
        source = Path(vault_path)
        if not source.exists():
            raise BackupError(f"Vault file not found: {vault_path}")

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        backup_name = f"{source.stem}_{timestamp}.enc.bak"
        dest = self.backup_dir / backup_name
        shutil.copy2(source, dest)

        index = self._load_index()
        index.append({
            "file": backup_name,
            "source": str(source),
            "timestamp": timestamp,
            "label": label,
        })

        if len(index) > self.MAX_BACKUPS:
            oldest = index.pop(0)
            old_file = self.backup_dir / oldest["file"]
            if old_file.exists():
                old_file.unlink()

        self._save_index(index)
        return str(dest)

    def list_backups(self) -> list:
        """Return list of backup metadata entries."""
        return self._load_index()

    def restore_backup(self, backup_name: str, target_path: str) -> None:
        """Restore a named backup to the target path."""
        backup_file = self.backup_dir / backup_name
        if not backup_file.exists():
            raise BackupError(f"Backup not found: {backup_name}")
        shutil.copy2(backup_file, target_path)
