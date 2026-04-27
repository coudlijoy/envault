"""CLI entry point for envault."""

import click

from envault.config import Config, ConfigError
from envault.crypto import generate_key
from envault.vault import Vault, VaultError
from envault.sync import SyncManager, SyncError


@click.group()
def cli():
    """envault — encrypt and sync .env files across your team."""
    pass


@cli.command()
def keygen():
    """Generate a new shared encryption key."""
    key = generate_key()
    click.echo(f"Generated key: {key}")
    click.echo("Share this key securely with your team.")


@cli.command(name="init")
@click.option("--env-file", default=".env", show_default=True, help="Path to the .env file.")
@click.option("--vault-file", default=".env.vault", show_default=True, help="Path to the vault file.")
@click.option("--shared-dir", default="", help="Shared directory for vault sync.")
def init_cmd(env_file, vault_file, shared_dir):
    """Initialise envault configuration in the current directory."""
    try:
        config = Config()
        config.init(env_file=env_file, vault_file=vault_file, shared_dir=shared_dir)
        click.echo(f"Initialised envault config at .envault.json")
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("key")
@click.option("--config-dir", default=".", hidden=True)
def lock(key, config_dir):
    """Encrypt the .env file into the vault."""
    try:
        config = Config(project_dir=config_dir).load()
        vault = Vault(key, env_path=config.env_file, vault_path=config.vault_file)
        vault.lock()
        click.echo(f"Locked {config.env_file} → {config.vault_file}")
    except (ConfigError, VaultError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("key")
@click.option("--config-dir", default=".", hidden=True)
def unlock(key, config_dir):
    """Decrypt the vault file into .env."""
    try:
        config = Config(project_dir=config_dir).load()
        vault = Vault(key, env_path=config.env_file, vault_path=config.vault_file)
        vault.unlock()
        click.echo(f"Unlocked {config.vault_file} → {config.env_file}")
    except (ConfigError, VaultError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("key")
@click.option("--config-dir", default=".", hidden=True)
def push(key, config_dir):
    """Lock and push the vault to the shared directory."""
    try:
        config = Config(project_dir=config_dir).load()
        vault = Vault(key, env_path=config.env_file, vault_path=config.vault_file)
        vault.lock()
        manager = SyncManager(key, shared_dir=config.shared_dir, vault_path=config.vault_file)
        manager.push()
        click.echo("Vault pushed to shared directory.")
    except (ConfigError, VaultError, SyncError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("key")
@click.option("--config-dir", default=".", hidden=True)
def pull(key, config_dir):
    """Pull the vault from the shared directory and unlock."""
    try:
        config = Config(project_dir=config_dir).load()
        manager = SyncManager(key, shared_dir=config.shared_dir, vault_path=config.vault_file)
        manager.pull()
        vault = Vault(key, env_path=config.env_file, vault_path=config.vault_file)
        vault.unlock()
        click.echo("Vault pulled and unlocked.")
    except (ConfigError, VaultError, SyncError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
