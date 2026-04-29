"""CLI commands for key rotation in envault."""

import click
from envault.rotation import KeyRotator, RotationError
from envault.config import Config, ConfigError


@click.group()
def rotation():
    """Key rotation commands."""


@rotation.command("rotate")
@click.argument("vault_path", default=".env.vault")
@click.option("--key", envvar="ENVAULT_KEY", required=True, help="Current encryption key.")
@click.option("--new-key", default=None, help="New key to rotate to (auto-generated if omitted).")
def rotate_cmd(vault_path, key, new_key):
    """Rotate the encryption key for a vault."""
    rotator = KeyRotator(vault_path)
    try:
        result_key = rotator.rotate(key, new_key=new_key)
        click.echo(click.style("Key rotated successfully.", fg="green"))
        click.echo(f"New key: {result_key}")
        click.echo(click.style("Update ENVAULT_KEY for all team members.", fg="yellow"))
    except RotationError as e:
        click.echo(click.style(f"Rotation failed: {e}", fg="red"), err=True)
        raise SystemExit(1)


@rotation.command("history")
@click.argument("vault_path", default=".env.vault")
def history_cmd(vault_path):
    """Show key rotation history for a vault."""
    rotator = KeyRotator(vault_path)
    events = rotator.rotation_history()
    if not events:
        click.echo("No rotation history found.")
        return
    click.echo(f"Rotation history for {vault_path}:")
    for i, event in enumerate(events, 1):
        click.echo(f"  {i}. {event['rotated_at']}")
