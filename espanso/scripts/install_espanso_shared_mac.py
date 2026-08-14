#!/usr/bin/env python3
"""Install Dropbox-backed shared Espanso matches on a Mac."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml


LABEL = "com.user.espanso-shared-reload"
ESPANSO_LABEL = "com.federicoterzi.espanso"
SCRIPT_DIR = Path(__file__).resolve().parent
SEED_FILE = SCRIPT_DIR.parent / "mac-config" / "match" / "base.yml"
RELOADER = SCRIPT_DIR / "reload_espanso_shared.py"
DEFAULT_LIVE = (
    Path.home() / "Library" / "Application Support" / "espanso" / "match" / "base.yml"
)
RUNTIME_DIR = Path.home() / "Library" / "Application Support" / "espanso-shared-reload"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
VALIDATION_MODES = ("strict", "file-provider-degraded")


def discover_dropbox_root() -> Path:
    info_file = Path.home() / ".dropbox" / "info.json"
    try:
        info = json.loads(info_file.read_text(encoding="utf-8"))
        for account in ("personal", "business"):
            configured = info.get(account, {}).get("path")
            if configured and Path(configured).is_dir():
                return Path(configured).resolve()
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
        pass

    legacy = Path.home() / "Dropbox"
    if legacy.is_symlink() and legacy.resolve().is_dir():
        return legacy.resolve()
    cloud = Path.home() / "Library" / "CloudStorage" / "Dropbox"
    if cloud.is_dir():
        return cloud.resolve()
    raise RuntimeError("Dropbox root not found; install or sign in to Dropbox first")


def default_source() -> Path:
    return discover_dropbox_root() / "espanso" / "base.yml"


def validate_match_file(path: Path) -> None:
    program = """
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
payload = yaml.safe_load(path.read_text(encoding="utf-8"))
if not isinstance(payload, dict) or not isinstance(payload.get("matches"), list):
    raise RuntimeError(f"invalid Espanso match structure: {path}")
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown error"
        raise RuntimeError(f"invalid Espanso match file: {path}: {detail}")


def file_digest(path: Path) -> str:
    result = subprocess.run(
        ["/usr/bin/shasum", "-a", "256", str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout.split(maxsplit=1)[0]


def file_fingerprint(path: Path) -> str:
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


def atomic_symlink(target: Path, link: Path) -> None:
    if target.absolute() == link.absolute():
        raise RuntimeError("source and live paths must be different")
    temporary = link.with_name(f".{link.name}.new.{os.getpid()}")
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, link)


def unique_backup(live: Path) -> Path | None:
    if not live.exists():
        return None
    backup_dir = live.parents[1] / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"base.pre-dropbox.{time.time_ns()}.yml"
    shutil.copy2(live.resolve(), backup)
    return backup


def launch_agent_payload(
    source: Path,
    live: Path,
    installed_reloader: Path,
    validation_mode: str,
) -> dict:
    log_path = Path.home() / "Library" / "Logs" / "espanso-shared-reload.log"
    return {
        "Label": LABEL,
        "ProgramArguments": [
            sys.executable,
            str(installed_reloader),
            "--source",
            str(source),
            "--live",
            str(live),
            "--validation-mode",
            validation_mode,
        ],
        "RunAtLoad": True,
        "WatchPaths": [str(source.parent)],
        "StartInterval": 300,
        "ProcessType": "Background",
        "ThrottleInterval": 5,
        "StandardOutPath": str(log_path),
        "StandardErrorPath": str(log_path),
    }


def run_launchctl(arguments: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["launchctl", *arguments],
        check=check,
        capture_output=True,
        text=True,
        timeout=15,
    )


def service_registered(label: str) -> bool:
    domain = f"gui/{os.getuid()}/{label}"
    result = run_launchctl(["print", domain], check=False)
    return result.returncode == 0


def wait_for_agent_success(domain: str, *, timeout_seconds: float = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_output = ""
    while time.monotonic() < deadline:
        result = run_launchctl(["print", f"{domain}/{LABEL}"], check=False)
        last_output = result.stdout
        if result.returncode == 0:
            state = next(
                (
                    line.split("=", 1)[1].strip()
                    for line in result.stdout.splitlines()
                    if line.strip().startswith("state =")
                ),
                None,
            )
            last_exit = next(
                (
                    line.split("=", 1)[1].strip()
                    for line in result.stdout.splitlines()
                    if line.strip().startswith("last exit code =")
                ),
                None,
            )
            if state == "not running" and last_exit == "0":
                return
            if state == "not running" and last_exit not in {None, "(never exited)"}:
                raise RuntimeError(f"background reload agent exited with code {last_exit}")
        time.sleep(0.25)
    raise RuntimeError(
        f"background reload agent did not complete within {timeout_seconds}s: {last_output.strip()}"
    )


def restore_path(path: Path, old_target: str | None, old_bytes: bytes | None) -> None:
    path.unlink(missing_ok=True)
    if old_target is not None:
        path.symlink_to(old_target)
    elif old_bytes is not None:
        path.write_bytes(old_bytes)


def install(source: Path, live: Path, *, validation_mode: str = "strict") -> None:
    if validation_mode not in VALIDATION_MODES:
        raise ValueError(f"invalid validation mode: {validation_mode}")
    if not SEED_FILE.is_file() or not RELOADER.is_file():
        raise RuntimeError("installer assets are missing from the tools repo")
    if not service_registered(ESPANSO_LABEL):
        raise RuntimeError("Espanso service is not registered; finish Espanso onboarding first")
    if source.exists() and not source.is_file():
        raise RuntimeError(f"Dropbox source is not a file: {source}")
    if source.absolute() == live.absolute():
        raise RuntimeError("source and live paths must be different")

    already_linked = live.is_symlink() and live.exists() and live.resolve() == source.resolve()

    source.parent.mkdir(parents=True, exist_ok=True)
    source_created = False
    if not source.exists():
        seed = live.resolve() if live.exists() else SEED_FILE
        shutil.copy2(seed, source)
        source_created = True
        print(f"created Dropbox canonical config from {seed}: {source}")
    elif live.exists() and not already_linked:
        if file_digest(live.resolve()) != file_digest(source):
            raise RuntimeError(
                "existing Dropbox and live configs differ; merge them explicitly before installing"
            )
    validation_fingerprint = file_fingerprint(source)
    try:
        validate_match_file(source)
    except subprocess.TimeoutExpired:
        if source_created:
            source.unlink(missing_ok=True)
        if validation_mode != "file-provider-degraded" or not already_linked:
            raise RuntimeError(
                "Dropbox source validation timed out; no installation changes were made"
            )
        print(
            "WARNING: Dropbox validation unavailable in this launch context; "
            "continuing idempotent runtime update for the existing live symlink"
        )
    except (OSError, RuntimeError, yaml.YAMLError):
        if source_created:
            source.unlink(missing_ok=True)
        raise
    if file_fingerprint(source) != validation_fingerprint:
        if source_created:
            source.unlink(missing_ok=True)
        raise RuntimeError("Dropbox source changed during validation; no changes were installed")

    live.parent.mkdir(parents=True, exist_ok=True)
    backup = None if already_linked else unique_backup(live)
    old_target = os.readlink(live) if live.is_symlink() else None
    old_live_bytes = live.read_bytes() if live.exists() and not live.is_symlink() else None

    plist_path = LAUNCH_AGENTS_DIR / f"{LABEL}.plist"
    old_plist = plist_path.read_bytes() if plist_path.is_file() else None
    installed_reloader = RUNTIME_DIR / "reload_espanso_shared.py"
    old_reloader = installed_reloader.read_bytes() if installed_reloader.is_file() else None
    domain = f"gui/{os.getuid()}"

    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RELOADER, installed_reloader)
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_bytes(
            plistlib.dumps(
                launch_agent_payload(source, live, installed_reloader, validation_mode),
                sort_keys=False,
            )
        )
        atomic_symlink(source, live)
        run_launchctl(["bootout", f"{domain}/{LABEL}"], check=False)
        run_launchctl(["bootstrap", domain, str(plist_path)], check=True)
        wait_for_agent_success(domain)
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        rollback_failures: list[str] = []

        def rollback(label: str, operation) -> bool:
            try:
                operation()
                return True
            except (OSError, subprocess.SubprocessError, RuntimeError) as rollback_error:
                rollback_failures.append(f"{label}: {rollback_error}")
                return False

        rollback(
            "bootout new agent",
            lambda: run_launchctl(["bootout", f"{domain}/{LABEL}"], check=False),
        )
        live_restored = rollback(
            "restore live config",
            lambda: restore_path(live, old_target, old_live_bytes),
        )
        if old_plist is None:
            rollback("remove new plist", lambda: plist_path.unlink(missing_ok=True))
        else:
            rollback("restore old plist", lambda: plist_path.write_bytes(old_plist))
        if old_reloader is None:
            rollback("remove new reloader", lambda: installed_reloader.unlink(missing_ok=True))
        else:
            rollback("restore old reloader", lambda: installed_reloader.write_bytes(old_reloader))
        if old_plist is not None:
            rollback(
                "bootstrap old agent",
                lambda: run_launchctl(["bootstrap", domain, str(plist_path)], check=True),
            )
        if source_created:
            if live_restored:
                rollback("remove new Dropbox source", lambda: source.unlink(missing_ok=True))
            else:
                rollback_failures.append(
                    f"preserved new Dropbox source for manual recovery: {source}"
                )
        if rollback_failures:
            raise RuntimeError(
                f"installation failed: {error}; rollback failures: "
                + "; ".join(rollback_failures)
            ) from error
        raise

    print(f"linked Espanso live config: {live} -> {source}")
    if backup:
        print(f"backed up previous live config: {backup}")
    print(f"registered background reload agent: {LABEL}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--live", type=Path, default=DEFAULT_LIVE)
    parser.add_argument("--validation-mode", choices=VALIDATION_MODES, default="strict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source = args.source.expanduser() if args.source else default_source()
        install(source, args.live.expanduser(), validation_mode=args.validation_mode)
    except (RuntimeError, OSError, subprocess.SubprocessError, yaml.YAMLError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
