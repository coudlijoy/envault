"""Tests for envault.config module."""

import json
import pytest
from pathlib import Path

from envault.config import Config, ConfigError, CONFIG_FILENAME


@pytest.fixture
def tmp_project(tmp_path):
    """Return a temporary project directory."""
    return tmp_path


@pytest.fixture
def config(tmp_project):
    return Config(project_dir=str(tmp_project))


class TestConfigInit:
    def test_init_creates_config_file(self, config, tmp_project):
        config.init()
        assert (tmp_project / CONFIG_FILENAME).exists()

    def test_init_writes_correct_defaults(self, config, tmp_project):
        config.init()
        data = json.loads((tmp_project / CONFIG_FILENAME).read_text())
        assert data["env_file"] == ".env"
        assert data["vault_file"] == ".env.vault"
        assert data["shared_dir"] == ""

    def test_init_custom_values(self, config, tmp_project):
        config.init(env_file=".env.prod", vault_file="prod.vault", shared_dir="/shared")
        data = json.loads((tmp_project / CONFIG_FILENAME).read_text())
        assert data["env_file"] == ".env.prod"
        assert data["vault_file"] == "prod.vault"
        assert data["shared_dir"] == "/shared"

    def test_init_raises_if_already_exists(self, config):
        config.init()
        with pytest.raises(ConfigError, match="already exists"):
            config.init()


class TestConfigLoad:
    def test_load_raises_if_missing(self, config):
        with pytest.raises(ConfigError, match="No config file found"):
            config.load()

    def test_load_returns_self(self, config):
        config.init()
        result = config.load()
        assert result is config

    def test_load_populates_properties(self, config):
        config.init(env_file=".env.staging", vault_file="staging.vault", shared_dir="/mnt")
        fresh = Config(project_dir=str(config.project_dir)).load()
        assert fresh.env_file == ".env.staging"
        assert fresh.vault_file == "staging.vault"
        assert fresh.shared_dir == "/mnt"


class TestConfigProperties:
    def test_as_dict_returns_all_keys(self, config):
        config.init(shared_dir="/team")
        config.load()
        d = config.as_dict()
        assert set(d.keys()) == {"env_file", "vault_file", "shared_dir"}

    def test_defaults_without_load(self, config):
        assert config.env_file == ".env"
        assert config.vault_file == ".env.vault"
        assert config.shared_dir == ""
