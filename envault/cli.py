"""CLI entry point for envault using Click."""

import sys
import click
from pathlib import Path

from envault.vault import Vault, VaultError
from envault.crypto import generate_key


@click.group()
@click.version_option(version="0.1.0", prog_name="envault")
def cli():
    """envault — Encrypt and sync .env files using a shared key."""
    pass


@cli.command()
def keygen():
    """Generate a new shared encryption key."""
    key = generate_key()
    click.echo(f"Generated key: {key}")
    click.echo("Store this key securely and share it with your team.", err=True)


@cli.command()
@click.argument("env_file", default=".env", type=click.Path(exists=True))
@click.option("--key", envvar="ENVAULT_KEY", required=True, help="Shared encryption key.")
@click.option("--output", "-o", default=None, help="Output path for the vault file.")
def lock(env_file, key, output):
    """Encrypt an .env file into a vault."""
    env_path = Path(env_file)
    vault_path = Path(output) if output else env_path.with_suffix(".vault")

    try:
        vault = Vault(vault_path, key)
        vault.lock(env_path)
        click.echo(f"Locked '{env_path}' -> '{vault_path}'")
    except VaultError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("vault_file", default=".env.vault", type=click.Path(exists=True))
@click.option("--key", envvar="ENVAULT_KEY", required=True, help="Shared encryption key.")
@click.option("--output", "-o", default=None, help="Output path for the decrypted .env file.")
def unlock(vault_file, key, output):
    """Decrypt a vault file into a .env file."""
    vault_path = Path(vault_file)
    env_path = Path(output) if output else vault_path.with_suffix(".env")

    try:
        vault = Vault(vault_path, key)
        vault.unlock(env_path)
        click.echo(f"Unlocked '{vault_path}' -> '{env_path}'")
    except VaultError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
