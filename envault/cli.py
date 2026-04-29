import click
from pathlib import Path
from envault.vault import Vault, VaultError
from envault.crypto import generate_key
from envault.config import Config, ConfigError
from envault.permissions import PermissionManager, PermissionError as EnvaultPermissionError


@click.group()
def cli():
    """envault — encrypt and sync .env files across your team."""
    pass


@cli.command("keygen")
def keygen():
    """Generate a new shared encryption key."""
    key = generate_key()
    click.echo(f"Generated key: {key}")


@cli.command("init")
@click.option("--shared-dir", default=".envault", help="Directory for shared vault files.")
def init_cmd(shared_dir):
    """Initialize envault in the current project."""
    try:
        config = Config(Path("."))
        config.init(shared_dir=shared_dir)
        click.echo(f"Initialized envault. Shared dir: {shared_dir}")
    except ConfigError as e:
        raise click.ClickException(str(e))


@cli.command("lock")
@click.argument("env_file", default=".env")
@click.option("--key", envvar="ENVAULT_KEY", required=True, help="Shared encryption key.")
@click.option("--user", envvar="ENVAULT_USER", default=None, help="Acting user for permission check.")
def lock(env_file, key, user):
    """Encrypt a .env file into the vault."""
    try:
        if user:
            pm = PermissionManager(Path(".envault") / "permissions.json")
            pm.require(user, "lock")
        vault = Vault(Path(env_file), key)
        vault.lock()
        click.echo(f"Locked {env_file}")
    except (VaultError, EnvaultPermissionError) as e:
        raise click.ClickException(str(e))


@cli.command("unlock")
@click.argument("env_file", default=".env")
@click.option("--key", envvar="ENVAULT_KEY", required=True, help="Shared encryption key.")
@click.option("--user", envvar="ENVAULT_USER", default=None, help="Acting user for permission check.")
def unlock(env_file, key, user):
    """Decrypt the vault back into a .env file."""
    try:
        if user:
            pm = PermissionManager(Path(".envault") / "permissions.json")
            pm.require(user, "unlock")
        vault = Vault(Path(env_file), key)
        vault.unlock()
        click.echo(f"Unlocked {env_file}")
    except (VaultError, EnvaultPermissionError) as e:
        raise click.ClickException(str(e))


@cli.group("users")
def users():
    """Manage team member permissions."""
    pass


@users.command("add")
@click.argument("username")
@click.argument("role", type=click.Choice(["admin", "editor", "viewer"]))
def users_add(username, role):
    """Grant a user a role."""
    try:
        pm = PermissionManager(Path(".envault") / "permissions.json")
        pm.add_user(username, role)
        click.echo(f"Added {username} as {role}")
    except EnvaultPermissionError as e:
        raise click.ClickException(str(e))


@users.command("remove")
@click.argument("username")
def users_remove(username):
    """Revoke a user's access."""
    try:
        pm = PermissionManager(Path(".envault") / "permissions.json")
        pm.remove_user(username)
        click.echo(f"Removed {username}")
    except EnvaultPermissionError as e:
        raise click.ClickException(str(e))


@users.command("list")
def users_list():
    """List all users and their roles."""
    pm = PermissionManager(Path(".envault") / "permissions.json")
    users_data = pm.list_users()
    if not users_data:
        click.echo("No users configured.")
    for entry in users_data:
        click.echo(f"{entry['user']}: {entry['role']}")
