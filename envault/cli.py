"""CLI entry point for envault."""

import click
from envault.vault import Vault, VaultError
from envault.sync import SyncManager, SyncError
from envault.crypto import generate_key


@click.group()
def cli():
    """envault — Encrypt and sync .env files across your team."""
    pass


@cli.command()
def keygen():
    """Generate a new shared encryption key."""
    key = generate_key()
    click.echo(f"Generated key: {key}")
    click.echo("Share this key securely with your team members.")


@cli.command()
@click.argument("env_file", default=".env")
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Shared encryption key.")
@click.option("--output", default=None, help="Output vault file path.")
def lock(env_file, key, output):
    """Encrypt a .env file into a vault."""
    try:
        vault = Vault()
        result = vault.lock(env_file, key)
        click.echo(f"Locked: {result}")
    except VaultError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("vault_file", default=".env.vault")
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Shared encryption key.")
@click.option("--output", default=None, help="Output .env file path.")
def unlock(vault_file, key, output):
    """Decrypt a vault file into a .env file."""
    try:
        vault = Vault()
        result = vault.unlock(vault_file, key, output)
        click.echo(f"Unlocked: {result}")
    except VaultError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("env_file", default=".env")
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Shared encryption key.")
@click.option("--shared-dir", required=True, envvar="ENVAULT_SHARED_DIR", help="Shared directory path.")
def push(env_file, key, shared_dir):
    """Encrypt and push .env to a shared directory."""
    try:
        vault = Vault()
        manager = SyncManager(shared_dir, vault)
        dest = manager.push(env_file, key)
        click.echo(f"Pushed vault to: {dest}")
    except (VaultError, SyncError) as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option("--key", required=True, envvar="ENVAULT_KEY", help="Shared encryption key.")
@click.option("--shared-dir", required=True, envvar="ENVAULT_SHARED_DIR", help="Shared directory path.")
@click.option("--output", default=None, help="Output .env file path.")
def pull(key, shared_dir, output):
    """Pull and decrypt .env from a shared directory."""
    try:
        vault = Vault()
        manager = SyncManager(shared_dir, vault)
        if manager.is_outdated():
            click.echo("Remote vault has changes. Pulling...")
        result = manager.pull(key, output)
        click.echo(f"Pulled and unlocked: {result}")
    except (VaultError, SyncError) as e:
        raise click.ClickException(str(e))
