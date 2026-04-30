"""CLI commands for vault backup and restore."""

import click
from pathlib import Path
from envault.backup import BackupManager, BackupError


@click.group()
def backup():
    """Backup and restore vault files."""
    pass


@backup.command("create")
@click.argument("vault_file")
@click.option("--label", default="", help="Optional label for this backup.")
def create_cmd(vault_file, label):
    """Create a backup of the specified vault file."""
    project_dir = Path(vault_file).parent
    try:
        manager = BackupManager(str(project_dir))
        dest = manager.create_backup(vault_file, label=label)
        click.echo(f"Backup created: {dest}")
    except BackupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@backup.command("list")
@click.option("--project-dir", default=".", help="Project directory.")
def list_cmd(project_dir):
    """List all available backups."""
    try:
        manager = BackupManager(project_dir)
        entries = manager.list_backups()
        if not entries:
            click.echo("No backups found.")
            return
        for entry in entries:
            label = f" [{entry['label']}]" if entry.get("label") else ""
            click.echo(f"{entry['timestamp']}  {entry['file']}{label}")
    except BackupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@backup.command("restore")
@click.argument("backup_name")
@click.argument("target_path")
@click.option("--project-dir", default=".", help="Project directory.")
def restore_cmd(backup_name, target_path, project_dir):
    """Restore a backup to the target vault path."""
    try:
        manager = BackupManager(project_dir)
        manager.restore_backup(backup_name, target_path)
        click.echo(f"Restored '{backup_name}' to '{target_path}'.")
    except BackupError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
