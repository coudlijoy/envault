"""Configuration management for envault."""

import json
import os
from pathlib import Path

CONFIG_FILENAME = ".envault.json"
DEFAULT_ENV_FILE = ".env"
DEFAULT_VAULT_FILE = ".env.vault"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """Manages per-project envault configuration stored in .envault.json."""

    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.config_path = self.project_dir / CONFIG_FILENAME
        self._data: dict = {}

    def load(self) -> "Config":
        """Load configuration from disk."""
        if not self.config_path.exists():
            raise ConfigError(
                f"No config file found at {self.config_path}. "
                "Run 'envault init' to create one."
            )
        with open(self.config_path, "r") as f:
            self._data = json.load(f)
        return self

    def save(self) -> None:
        """Persist configuration to disk."""
        with open(self.config_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def init(self, env_file: str = DEFAULT_ENV_FILE,
             vault_file: str = DEFAULT_VAULT_FILE,
             shared_dir: str = "") -> None:
        """Initialise a new configuration file."""
        if self.config_path.exists():
            raise ConfigError(f"Config already exists at {self.config_path}.")
        self._data = {
            "env_file": env_file,
            "vault_file": vault_file,
            "shared_dir": shared_dir,
        }
        self.save()

    @property
    def env_file(self) -> str:
        return self._data.get("env_file", DEFAULT_ENV_FILE)

    @property
    def vault_file(self) -> str:
        return self._data.get("vault_file", DEFAULT_VAULT_FILE)

    @property
    def shared_dir(self) -> str:
        return self._data.get("shared_dir", "")

    def as_dict(self) -> dict:
        return dict(self._data)
