# src/cli.py
import os
import signal
import sys
from pathlib import Path

import typer
import uvicorn

cli = typer.Typer()

PID_FILE = Path("../.wms-copilot.pid")


@cli.command()
def start(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
):
    """Start the WMS Copilot API server."""
    if PID_FILE.exists():
        existing_pid = PID_FILE.read_text().strip()
        if _is_running(int(existing_pid)):
            typer.echo(f"❌ Already running (PID {existing_pid}). Use `wms-copilot stop` first.")
            raise typer.Exit(code=1)
        else:
            # Stale PID file from a crashed/killed process
            PID_FILE.unlink()

    PID_FILE.write_text(str(os.getpid()))
    typer.echo(f"✅ Starting on http://{host}:{port} (PID {os.getpid()})")

    try:
        uvicorn.run("api.app:app", host=host, port=port)
    finally:
        # Clean up PID file when uvicorn exits (Ctrl+C, error, etc.)
        if PID_FILE.exists():
            PID_FILE.unlink()


@cli.command()
def stop():
    """Stop the running WMS Copilot server."""
    if not PID_FILE.exists():
        typer.echo("⚠️  No PID file found. Server may not be running.")
        raise typer.Exit(code=1)

    pid = int(PID_FILE.read_text().strip())

    if not _is_running(pid):
        typer.echo(f"⚠️  Process {pid} is not running. Removing stale PID file.")
        PID_FILE.unlink()
        raise typer.Exit(code=1)

    typer.echo(f"🛑 Stopping server (PID {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)   # graceful shutdown signal
    except ProcessLookupError:
        typer.echo("Process already gone.")
        PID_FILE.unlink()
        return
    except PermissionError:
        typer.echo(f"❌ Permission denied. Try: sudo kill {pid}")
        raise typer.Exit(code=1)

    typer.echo("✅ Stop signal sent. Server will shut down gracefully.")


@cli.command()
def status():
    """Check if the server is running."""
    if not PID_FILE.exists():
        typer.echo("⚪ Not running (no PID file)")
        return

    pid = int(PID_FILE.read_text().strip())
    if _is_running(pid):
        typer.echo(f"🟢 Running (PID {pid})")
    else:
        typer.echo(f"🔴 PID file exists but process {pid} is dead. Removing stale file.")
        PID_FILE.unlink()


def _is_running(pid: int) -> bool:
    """Cross-platform check: is this PID currently a running process?"""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)   # signal 0 = "do nothing, just check if process exists"
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't own it — still "running" for our purposes
        return True
    return True


if __name__ == "__main__":
    cli()