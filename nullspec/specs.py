"""Spec discovery, validation and task parsing.

A spec lives in ``.kiro/specs/<name>/`` and must contain a single markdown file with three
sections — ``## Requirements``, ``## Design`` and ``## Tasks``. Tasks are markdown checkboxes,
which makes the plan auditable in git.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SPEC_DIRS = ("requirements.md", "design.md", "tasks.md")
REQUIRED_SECTIONS = ("## Requirements", "## Design", "## Tasks")
CHECKBOX = re.compile(r"^\s*-\s*\[(?P<mark>[ xX])\]\s*(?P<text>.+?)\s*$")
HEADING = re.compile(r"^#{2,3}\s+")


@dataclass(frozen=True)
class Task:
    text: str
    done: bool
    line: int

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{'[x]' if self.done else '[ ]'} {self.text}"


@dataclass
class Spec:
    name: str
    path: Path
    text: str = ""
    tasks: list[Task] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    @property
    def done(self) -> int:
        return sum(1 for task in self.tasks if task.done)

    @property
    def total(self) -> int:
        return len(self.tasks)


def spec_root(root: Path | str = ".") -> Path:
    return Path(root) / ".kiro" / "specs"


def discover(root: Path | str = ".") -> list[Spec]:
    """Return every spec folder found under ``.kiro/specs``."""
    base = spec_root(root)
    if not base.is_dir():
        return []
    specs: list[Spec] = []
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        files = [p for p in folder.glob("*.md")]
        if not files:
            specs.append(Spec(folder.name, folder, problems=["no markdown file"]))
            continue
        # Prefer the conventional single-file layout, otherwise concatenate deterministically.
        ordered = sorted(files, key=lambda p: (p.name not in SPEC_DIRS, p.name))
        text = "\n\n".join(p.read_text(encoding="utf-8") for p in ordered)
        spec = Spec(folder.name, folder, text=text)
        spec.problems.extend(validate(text))
        spec.tasks = parse_tasks(text)
        if spec.total == 0:
            spec.problems.append("no checkbox tasks under '## Tasks'")
        specs.append(spec)
    return specs


def validate(text: str) -> list[str]:
    """Return human-readable problems with a spec body."""
    problems = [f"missing section {section!r}" for section in REQUIRED_SECTIONS if section not in text]
    requirements = _section(text, "## Requirements")
    if requirements and "acceptance" not in requirements.lower():
        problems.append("requirements have no acceptance criteria")
    design = _section(text, "## Design")
    if design and len(design.split()) < 20:
        problems.append("design section is too thin (<20 words)")
    return problems


def _section(text: str, heading: str) -> str:
    """Body of a ``##`` section, stopping at the next ``##`` heading."""
    lines = text.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        if line.strip().startswith("## "):
            if inside:
                break
            inside = line.strip().startswith(heading)
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def parse_tasks(text: str) -> list[Task]:
    body = _section(text, "## Tasks")
    if not body:
        return []
    tasks: list[Task] = []
    for offset, line in enumerate(body.splitlines(), start=1):
        match = CHECKBOX.match(line)
        if match:
            tasks.append(Task(match.group("text"), match.group("mark").lower() == "x", offset))
    return tasks
