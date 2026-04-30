"""Pre/post hooks for vault operations (lock, unlock, sync)."""

import subprocess
from pathlib import Path
from typing import Optional


class HookError(Exception):
    pass


HOOK_EVENTS = ("pre-lock", "post-lock", "pre-unlock", "post-unlock", "pre-sync", "post-sync")


class HookManager:
    def __init__(self, hooks_dir: Path):
        self.hooks_dir = Path(hooks_dir)

    def register(self, event: str, script_path: Path) -> None:
        if event not in HOOK_EVENTS:
            raise HookError(f"Unknown hook event '{event}'. Valid events: {HOOK_EVENTS}")
        script_path = Path(script_path)
        if not script_path.exists():
            raise HookError(f"Hook script not found: {script_path}")
        self.hooks_dir.mkdir(parents=True, exist_ok=True)
        dest = self.hooks_dir / event
        dest.write_text(script_path.read_text())
        dest.chmod(0o755)

    def run(self, event: str, env: Optional[dict] = None) -> Optional[str]:
        if event not in HOOK_EVENTS:
            raise HookError(f"Unknown hook event '{event}'")
        hook_script = self.hooks_dir / event
        if not hook_script.exists():
            return None
        try:
            result = subprocess.run(
                [str(hook_script)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            if result.returncode != 0:
                raise HookError(
                    f"Hook '{event}' failed (exit {result.returncode}): {result.stderr.strip()}"
                )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise HookError(f"Hook '{event}' timed out after 30 seconds")

    def list_hooks(self) -> list:
        if not self.hooks_dir.exists():
            return []
        return [p.name for p in self.hooks_dir.iterdir() if p.name in HOOK_EVENTS]

    def remove(self, event: str) -> bool:
        hook_script = self.hooks_dir / event
        if hook_script.exists():
            hook_script.unlink()
            return True
        return False
