from __future__ import annotations

from pathlib import Path

from .models import FeatureRequest


def parse_feature_request(path: str | Path) -> FeatureRequest:
    feature_path = Path(path)
    text = feature_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Feature request is empty: {feature_path}")

    lines = [line.rstrip() for line in text.splitlines()]
    title = _first_heading(lines) or feature_path.stem.replace("_", " ").replace("-", " ").title()
    requirements = _bullet_items(lines)
    summary = _summary(lines, title)

    return FeatureRequest(
        title=title,
        summary=summary,
        requirements=requirements,
        raw_text=text,
    )


def _first_heading(lines: list[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def _bullet_items(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            bullets.append(stripped[2:].strip())
    return bullets


def _summary(lines: list[str], title: str) -> str:
    paragraphs: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(("- ", "* ")):
            continue
        paragraphs.append(stripped)
    return " ".join(paragraphs) if paragraphs else title
