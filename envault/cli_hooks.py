"""CLI commands for managing envault hooks."""

import click
from pathlib import Path
from envault.hooks import HookManager, HOOK_EVENTS, HookError


@click.group()
def hooks():
    """Manage pre/post operation hooks."""
    pass


@hooks.command("register")
@click.argument("event", type=click.Choice(HOOK_EVENTS))
@click.argument("script", type=click.Path(exists=True))
@click.option("--hooks-dir", default=".envault/hooks", help="Directory to store hooks.")
def register_cmd(event, script, hooks_dir):
    """Register a hook script for an event."""
    try:
        manager = HookManager(Path(hooks_dir))
        manager.register(event, Path(script))
        click.echo(f"Hook registered: {event} -> {script}")
    except HookError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@hooks.command("list")
@click.option("--hooks-dir", default=".envault/hooks", help="Directory to store hooks.")
def list_cmd(hooks_dir):
    """List all registered hooks."""
    manager = HookManager(Path(hooks_dir))
    registered = manager.list_hooks()
    if not registered:
        click.echo("No hooks registered.")
    else:
        click.echo("Registered hooks:")
        for event in registered:
            click.echo(f"  {event}")


@hooks.command("remove")
@click.argument("event", type=click.Choice(HOOK_EVENTS))
@click.option("--hooks-dir", default=".envault/hooks", help="Directory to store hooks.")
def remove_cmd(event, hooks_dir):
    """Remove a registered hook."""
    manager = HookManager(Path(hooks_dir))
    removed = manager.remove(event)
    if removed:
        click.echo(f"Hook removed: {event}")
    else:
        click.echo(f"No hook registered for event: {event}")
