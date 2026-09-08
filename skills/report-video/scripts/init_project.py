#!/usr/bin/env python3
"""Initialize a portable report-video project from an SRT file."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


TIMECODE_RE = re.compile(
    r"^\s*\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*"
    r"\d{2}:\d{2}:\d{2}[,.]\d{3}(?:\s+.*)?$"
)
FORMATTING_TAG_RE = re.compile(
    r"""
    (?:
        </?(?:b|i|u)\s*>
        | </font\s*>
        | <font
          (?:\s+(?:color|face|size)\s*=\s*(?:"[^"<>]+"|'[^'<>]+'))+
          \s*>
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
UNSAFE_ID_RE = re.compile(r"[^A-Za-z0-9]+")


def sanitize_project_id(value: str) -> str:
    """Return a lowercase, path-safe identifier made of ASCII and hyphens."""
    sanitized = UNSAFE_ID_RE.sub("-", value).strip("-").lower()
    return sanitized or "project"


def srt_to_script(srt_text: str) -> str:
    """Extract ordered cue text, joining lines within each cue."""
    cues: list[str] = []
    current: list[str] = []
    at_cue_start = True

    def flush() -> None:
        if current:
            cue = " ".join(current).strip()
            if cue:
                cues.append(cue)
            current.clear()

    normalized = srt_text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            flush()
            at_cue_start = True
        elif at_cue_start and line.isdigit():
            at_cue_start = False
            continue
        else:
            at_cue_start = False
            if TIMECODE_RE.fullmatch(line):
                continue
            text = FORMATTING_TAG_RE.sub("", line).strip()
            if text:
                current.append(text)

    flush()
    return "\n".join(cues)


def _asset_library_value(project: Path, asset_library: Path | None) -> str | None:
    if asset_library is None:
        return None

    resolved = asset_library.expanduser().resolve()
    try:
        return Path(os.path.relpath(resolved, project)).as_posix()
    except ValueError:
        return resolved.as_posix()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def initialize_project(
    factory_root: Path,
    srt_path: Path,
    *,
    project_id: str | None = None,
    title: str | None = None,
    aspect_ratio: str = "16:9",
    subtitle_burn_in: bool = True,
    asset_library: Path | None = None,
) -> Path:
    """Create and return a new projects/<project-id> directory."""
    factory_root = factory_root.expanduser().resolve()
    srt_path = srt_path.expanduser().resolve()

    if not srt_path.exists():
        raise FileNotFoundError(f"SRT not found: {srt_path}")
    if not srt_path.is_file():
        raise ValueError(f"Expected a regular SRT file, got: {srt_path}")
    if srt_path.suffix.lower() != ".srt":
        raise ValueError(f"Expected .srt input, got: {srt_path.name}")

    source_bytes = srt_path.read_bytes()
    srt_text = source_bytes.decode("utf-8-sig")
    pid = sanitize_project_id(srt_path.stem if project_id is None else project_id)
    project = factory_root / "projects" / pid

    if project.exists():
        raise FileExistsError(f"Project already exists: {project}")

    (project / "input").mkdir(parents=True)
    (project / "output/preview").mkdir(parents=True)
    (project / "output/final").mkdir(parents=True)

    (project / "input/subtitles.srt").write_bytes(source_bytes)
    script = srt_to_script(srt_text)
    (project / "input/script.txt").write_text(
        script + ("\n" if script else ""), encoding="utf-8"
    )

    (project / "STORYBOARD.md").write_text(
        "# Storyboard\n\n"
        "Status: not started.\n\n"
        "Timing source: `input/subtitles.srt`\n\n"
        "No shots have been planned or assigned to a renderer.\n",
        encoding="utf-8",
    )

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    _write_json(
        project / "ASSET_MANIFEST.json",
        {"projectId": pid, "generatedAt": generated_at, "assets": []},
    )
    _write_json(
        project / "project.json",
        {
            "schemaVersion": 1,
            "projectId": pid,
            "title": srt_path.stem if title is None else title,
            "status": "initialized",
            "timingSource": "input/subtitles.srt",
            "script": "input/script.txt",
            "storyboard": "STORYBOARD.md",
            "assetManifest": "ASSET_MANIFEST.json",
            "renderOutput": None,
            "aspectRatio": aspect_ratio,
            "subtitleBurnIn": subtitle_burn_in,
            "assetLibrary": _asset_library_value(project, asset_library),
        },
    )
    return project


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a report-video project from an SRT"
    )
    parser.add_argument("srt", type=Path, help="Source SRT file")
    parser.add_argument(
        "--factory-root",
        type=Path,
        default=Path.cwd(),
        help="Root containing or receiving projects/",
    )
    parser.add_argument("--project-id")
    parser.add_argument("--title")
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--asset-library", type=Path)
    parser.add_argument("--no-burn-subtitles", action="store_true")
    args = parser.parse_args(argv)

    project = initialize_project(
        args.factory_root,
        args.srt,
        project_id=args.project_id,
        title=args.title,
        aspect_ratio=args.aspect_ratio,
        subtitle_burn_in=not args.no_burn_subtitles,
        asset_library=args.asset_library,
    )
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
