"""Scaffolding: `nullspec new-app <name> --purpose "..."` from skeleton/template."""

from __future__ import annotations

import shutil
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "skeleton" / "template"


class ScaffoldError(RuntimeError):
    """Scaffolding refused — target exists or template is missing."""


def new_app(name: str, purpose: str, root: Path | str = ".") -> Path:
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ScaffoldError(f"app name must be alphanumeric with - or _: {name!r}")
    if not TEMPLATE.is_dir():
        raise ScaffoldError(f"template missing: {TEMPLATE}")
    base = Path(root)
    target = base / "apps" / name
    spec_dir = base / ".kiro" / "specs" / name
    if target.exists() or spec_dir.exists():
        raise ScaffoldError(f"{name} already exists — refusing to overwrite")
    target.mkdir(parents=True)
    spec_dir.mkdir(parents=True)

    substitutions = {"{name}": name, "{purpose}": purpose}
    for source in TEMPLATE.iterdir():
        text = source.read_text(encoding="utf-8")
        for needle, value in substitutions.items():
            text = text.replace(needle, value)
        destination = spec_dir / "requirements.md" if source.name == "requirements.md" else target / source.name
        destination.write_text(text, encoding="utf-8")
    return target


def remove_app(name: str, root: Path | str = ".") -> None:  # pragma: no cover - manual helper
    base = Path(root)
    for path in (base / "apps" / name, base / ".kiro" / "specs" / name):
        shutil.rmtree(path, ignore_errors=True)
