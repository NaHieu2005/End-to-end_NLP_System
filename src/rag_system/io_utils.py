from __future__ import annotations

from pathlib import Path


def read_lines(path: str | Path) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()]


def write_lines(path: str | Path, lines: list[str]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_references(line: str) -> list[str]:
    return [part.strip() for part in line.split(";") if part.strip()]
