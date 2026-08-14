#!/usr/bin/env python3
"""Reload Espanso after the Dropbox-backed shared match file changes."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_SOURCE = Path.home() / "Dropbox" / "espanso" / "base.yml"
DEFAULT_LIVE = (
    Path.home()
    / "Library"
    / "Application Support"
    / "espanso"
    / "match"
    / "base.yml"
)
STATE_DIR = Path(
    os.environ.get(
        "ESPANSO_SHARED_STATE_DIR",
        Path.home() / "Library" / "Caches" / "espanso-shared-reload",
    )
)
VALIDATION_MODES = ("strict", "file-provider-degraded")


def log(message: str) -> None:
    print(f"{datetime.now().astimezone().isoformat(timespec='seconds')} {message}", flush=True)


def file_fingerprint(path: Path) -> str:
    """Identify Dropbox updates without opening File Provider file contents."""
    metadata = path.stat()
    return ":".join(
        str(value)
        for value in (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        )
    )


def espanso_binary() -> str:
    candidates = [
        shutil.which("espanso"),
        "/opt/homebrew/bin/espanso",
        "/usr/local/bin/espanso",
        "/Applications/Espanso.app/Contents/MacOS/espanso",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("espanso binary not found")


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )


def service_is_running(espanso: str) -> bool:
    result = subprocess.run(
        [espanso, "service", "status"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "espanso is running"


def load_state(state_file: Path) -> dict[str, str]:
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        fingerprint = payload.get("fingerprint")
        validation_status = payload.get("validation_status")
        if not isinstance(fingerprint, str) or validation_status not in {
            "validated",
            "degraded_pending",
        }:
            return {}
        return {
            "fingerprint": fingerprint,
            "validation_status": validation_status,
        }
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def store_state(state_file: Path, fingerprint: str, validation_status: str) -> None:
    if validation_status not in {"validated", "degraded_pending"}:
        raise ValueError(f"invalid validation status: {validation_status}")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_file.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "fingerprint": fingerprint,
                "validation_status": validation_status,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, state_file)


def reload_if_changed(
    source: Path,
    live: Path,
    *,
    force: bool = False,
    validation_mode: str = "strict",
) -> bool:
    if validation_mode not in VALIDATION_MODES:
        raise ValueError(f"invalid validation mode: {validation_mode}")
    if not source.is_file():
        log(f"source unavailable; keeping current worker state: {source}")
        return False
    if not live.is_symlink():
        raise RuntimeError(f"live match is not a symlink: {live}")
    if live.resolve() != source.resolve():
        raise RuntimeError(f"live match points to {live.resolve()}, expected {source.resolve()}")

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = STATE_DIR / "reload.lock"
    state_file = STATE_DIR / "state.json"
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        fingerprint = file_fingerprint(source)
        previous = load_state(state_file)
        same_fingerprint = previous.get("fingerprint") == fingerprint
        if (
            not force
            and same_fingerprint
            and previous.get("validation_status") == "validated"
        ):
            return False
        needs_notification = force or not same_fingerprint

        espanso = espanso_binary()
        # Parses every active match file without relying on the running worker.
        # Some Macs deny launchd ancestry content access to Dropbox File
        # Provider even though the GUI Espanso worker can read the same symlink.
        # A real parse error remains fatal; only an I/O timeout degrades to the
        # worker's own parser, and is always visible in the log.
        validation_status = "validated"
        try:
            run_checked([espanso, "match", "list"])
        except subprocess.TimeoutExpired:
            if validation_mode == "strict":
                raise
            validation_status = "degraded_pending"
            log(
                "WARNING: pre-validation timed out in explicit "
                "file-provider-degraded mode"
            )
        verified_fingerprint = file_fingerprint(source)
        if verified_fingerprint != fingerprint:
            raise RuntimeError("Dropbox source changed during validation; retrying next event")
        if not needs_notification:
            if validation_status == "validated":
                store_state(state_file, fingerprint, "validated")
                log(f"validated previously notified config fingerprint={fingerprint}")
            else:
                log(f"validation still pending for fingerprint={fingerprint}")
            return False

        if service_is_running(espanso):
            # The daemon watches the live config directory, not a symlink target.
            # Touching the link itself makes it reload the worker without stealing focus.
            os.utime(live, follow_symlinks=False)
        else:
            domain = f"gui/{os.getuid()}/com.federicoterzi.espanso"
            run_checked(["launchctl", "kickstart", domain])

        for _ in range(20):
            if service_is_running(espanso):
                break
            time.sleep(0.25)
        else:
            raise RuntimeError("espanso did not report running after config reload")

        store_state(state_file, fingerprint, validation_status)
        if validation_status == "validated":
            log(f"notified validated config fingerprint={fingerprint}")
        else:
            log(f"notified_unvalidated config fingerprint={fingerprint}")
        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--live", type=Path, default=DEFAULT_LIVE)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validation-mode", choices=VALIDATION_MODES, default="strict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        reload_if_changed(
            args.source.expanduser(),
            args.live.expanduser(),
            force=args.force,
            validation_mode=args.validation_mode,
        )
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        log(f"ERROR: {error}")
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.rstrip(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
