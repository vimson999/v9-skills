#!/usr/bin/env python3
"""Import originals into a portable shared media library and rebuild its catalog."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import unicodedata


LIBRARY_ID = "v9-asset-library"
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}
REPORT_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = VIDEO_SUFFIXES | IMAGE_SUFFIXES | REPORT_SUFFIXES
REVIEWED_FIELDS = (
    "description",
    "tags",
    "selectionStatus",
    "provenanceStatus",
    "licenseStatus",
    "resolutionWarning",
    "notes",
)
STORAGE_KINDS = {
    "video": "video",
    "images": "image",
    "reports": "report",
    "logos": "logo",
}
SELECTION_STATUSES = {"unreviewed", "candidate", "selected", "rejected", "backup"}
PROVENANCE_STATUSES = {"unknown", "probable", "verified"}
LICENSE_STATUSES = {"unverified", "confirmed", "restricted", "forbidden"}
RESERVED_PROJECT_ID_CHARACTERS = set('/\\<>:"|?*')


class LibraryBusyError(RuntimeError):
    """Raised when another process owns the library mutation lock."""


def _utc_now() -> tuple[datetime, str]:
    instant = datetime.now(timezone.utc)
    return instant, instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _library_path(library_root: Path, relative: str | Path) -> Path:
    """Return a contained path, rejecting symlinks in library-owned components."""
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Library path must be relative and contained: {relative}")
    candidate = library_root / relative
    current = library_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlinked library component is not allowed: {current}")
    try:
        candidate.resolve(strict=False).relative_to(library_root)
    except ValueError as error:
        raise ValueError(f"Library path resolves outside the library root: {candidate}") from error
    return candidate


def _write_library_json(library_root: Path, relative: str | Path, value: object) -> None:
    path = _library_path(library_root, relative)
    _write_json(path, value)


@contextmanager
def _library_lock(library_root: Path):
    """Hold a portable cross-process lock for all library mutations."""
    library_root = library_root.expanduser().resolve()
    library_root.mkdir(parents=True, exist_ok=True)
    lock_path = _library_path(library_root, ".intake.lock")
    handle = lock_path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError) as error:
        handle.close()
        raise LibraryBusyError(f"Asset library is busy: {library_root}") from error
    try:
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid={os.getpid()}\n".encode())
        handle.flush()
        os.fsync(handle.fileno())
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _read_json(path: Path, fallback: object) -> object:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _is_visible_relative(path: Path, root: Path) -> bool:
    return not any(part.startswith(".") for part in path.relative_to(root).parts)


def _safe_project_id(project_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", project_id).strip("-_").lower()
    return safe or "intake"


def _validate_default_project_id(project_id: str) -> None:
    if not isinstance(project_id, str) or not project_id or project_id != project_id.strip():
        raise ValueError("project_id must be a non-empty name without surrounding whitespace")
    if project_id in {".", ".."} or any(
        character in RESERVED_PROJECT_ID_CHARACTERS
        or unicodedata.category(character) == "Cc"
        for character in project_id
    ):
        raise ValueError("project_id must be a single path-safe directory name")


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def category_for_path(path: Path) -> str:
    """Return the raw storage category for a supported media path."""
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES and any(part.lower() == "logos" for part in path.parts[:-1]):
        return "logos"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in IMAGE_SUFFIXES:
        return "images"
    if suffix in REPORT_SUFFIXES:
        return "reports"
    raise ValueError(f"Unsupported media type: {path}")


def _initialize_library(library_root: Path) -> None:
    library_root = library_root.expanduser().resolve()
    directory_names = (
        "raw/video",
        "raw/images",
        "raw/reports",
        "raw/logos",
        "processed/video",
        "processed/images",
        "processed/thumbnails",
        "catalog/intake_logs",
    )
    file_names = (
        "catalog/assets.json",
        "catalog/metadata.json",
        "catalog/review_queue.json",
        "catalog/usage.json",
        "catalog/intake_log.json",
    )
    directories = [_library_path(library_root, relative) for relative in directory_names]
    files = [_library_path(library_root, relative) for relative in file_names]
    for path in directories:
        path.mkdir(parents=True, exist_ok=True)

    _, updated_at = _utc_now()
    initial_files = {
        "assets.json": {
            "schemaVersion": 1,
            "libraryId": LIBRARY_ID,
            "updatedAt": updated_at,
            "assets": [],
        },
        "metadata.json": {"schemaVersion": 1, "libraryId": LIBRARY_ID, "assets": {}},
        "review_queue.json": {
            "schemaVersion": 1,
            "libraryId": LIBRARY_ID,
            "updatedAt": updated_at,
            "assets": [],
        },
        "usage.json": {
            "schemaVersion": 1,
            "libraryId": LIBRARY_ID,
            "projects": {},
            "assets": {},
        },
        "intake_log.json": {
            "schemaVersion": 1,
            "libraryId": LIBRARY_ID,
            "updatedAt": updated_at,
            "importedCount": 0,
            "duplicateCount": 0,
            "ignoredCount": 0,
            "imported": [],
            "duplicates": [],
            "ignored": [],
        },
    }
    for path, value in zip(files, initial_files.values()):
        if not path.exists():
            _write_library_json(library_root, path.relative_to(library_root), value)


def initialize_library(library_root: Path) -> None:
    """Create the portable library structure without resetting durable catalog data."""
    library_root = library_root.expanduser().resolve()
    with _library_lock(library_root):
        _initialize_library(library_root)


def _raw_files(library_root: Path) -> list[Path]:
    raw_root = _library_path(library_root, "raw")
    paths = list(raw_root.rglob("*"))
    for path in paths:
        _library_path(library_root, path.relative_to(library_root))
    return sorted(
        (
            path
            for path in paths
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_SUFFIXES
            and _is_visible_relative(path, raw_root)
        ),
        key=lambda path: path.relative_to(library_root).as_posix(),
    )


def _review_reasons(asset: dict) -> list[str]:
    reasons = []
    if not asset["description"].strip():
        reasons.append("missing_description")
    if asset["selectionStatus"] in {"", "unknown", "unreviewed", "pending"}:
        reasons.append("selection_unreviewed")
    if asset["provenanceStatus"] in {"", "unknown", "unverified", "pending"}:
        reasons.append("provenance_unknown")
    if asset["licenseStatus"] in {"", "unknown", "unverified", "pending"}:
        reasons.append("license_unverified")
    return reasons


def _normalized_status(value: object, allowed: set[str], fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    normalized = value.strip().lower()
    return normalized if normalized in allowed else fallback


def _normalize_reviewed_fields(reviewed: object) -> dict:
    if not isinstance(reviewed, dict):
        return {}
    description = reviewed.get("description")
    tags = reviewed.get("tags")
    resolution_warning = reviewed.get("resolutionWarning")
    notes = reviewed.get("notes")
    return {
        "description": (
            description if isinstance(description, str) and description.strip() else ""
        ),
        "tags": (
            tags
            if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags)
            else []
        ),
        "selectionStatus": _normalized_status(
            reviewed.get("selectionStatus"), SELECTION_STATUSES, "unreviewed"
        ),
        "provenanceStatus": _normalized_status(
            reviewed.get("provenanceStatus"), PROVENANCE_STATUSES, "unknown"
        ),
        "licenseStatus": _normalized_status(
            reviewed.get("licenseStatus"), LICENSE_STATUSES, "unverified"
        ),
        "resolutionWarning": (
            resolution_warning
            if resolution_warning is None or isinstance(resolution_warning, str)
            else None
        ),
        "notes": notes if isinstance(notes, str) else "",
    }


def _rebuild_catalog(library_root: Path) -> dict:
    library_root = library_root.expanduser().resolve()
    _initialize_library(library_root)
    catalog_root = _library_path(library_root, "catalog")
    metadata = _read_json(
        catalog_root / "metadata.json",
        {"schemaVersion": 1, "libraryId": LIBRARY_ID, "assets": {}},
    )
    metadata_assets = metadata.get("assets", {}) if isinstance(metadata, dict) else {}

    assets = []
    seen_hashes = set()
    for path in _raw_files(library_root):
        digest = sha256_file(path)
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        relative = path.relative_to(library_root)
        category = category_for_path(relative)
        asset_id = f"asset-{digest[:16]}"
        asset = {
            "id": asset_id,
            "sha256": digest,
            "kind": STORAGE_KINDS[category],
            "path": relative.as_posix(),
            "fileName": path.name,
            "fileSizeBytes": path.stat().st_size,
            "description": "",
            "tags": [],
            "selectionStatus": "unreviewed",
            "provenanceStatus": "unknown",
            "licenseStatus": "unverified",
            "resolutionWarning": None,
            "notes": "",
        }
        reviewed = metadata_assets.get(asset_id, {}) if isinstance(metadata_assets, dict) else {}
        if isinstance(reviewed, dict):
            normalized = _normalize_reviewed_fields(reviewed)
            for field in REVIEWED_FIELDS:
                if field in reviewed:
                    asset[field] = normalized[field]
        assets.append(asset)

    assets.sort(key=lambda asset: (asset["id"], asset["path"]))
    _, updated_at = _utc_now()
    catalog = {
        "schemaVersion": 1,
        "libraryId": LIBRARY_ID,
        "updatedAt": updated_at,
        "assets": assets,
    }
    queue_assets = []
    for asset in assets:
        reasons = _review_reasons(asset)
        if reasons:
            queue_assets.append({"id": asset["id"], "path": asset["path"], "reasons": reasons})
    review_queue = {
        "schemaVersion": 1,
        "libraryId": LIBRARY_ID,
        "updatedAt": updated_at,
        "assets": queue_assets,
    }
    _write_library_json(library_root, "catalog/assets.json", catalog)
    _write_library_json(library_root, "catalog/review_queue.json", review_queue)
    return catalog


def rebuild_catalog(library_root: Path) -> dict:
    """Rebuild computed catalog data from disk while preserving reviewed metadata."""
    library_root = library_root.expanduser().resolve()
    with _library_lock(library_root):
        return _rebuild_catalog(library_root)


def _destination(raw_root: Path, category: str, source: Path, digest: str) -> Path:
    target = raw_root / category / source.name
    if not target.exists() or sha256_file(target) == digest:
        return target

    candidate = target.with_name(f"{source.stem}__{digest[:8]}{source.suffix}")
    counter = 2
    while candidate.exists() and sha256_file(candidate) != digest:
        candidate = target.with_name(
            f"{source.stem}__{digest[:8]}_{counter}{source.suffix}"
        )
        counter += 1
    return candidate


def _visible_files(source: Path) -> list[Path]:
    if not source.exists():
        return []
    if not source.is_dir():
        raise NotADirectoryError(source)
    return sorted(
        (
            path
            for path in source.rglob("*")
            if path.is_file() and _is_visible_relative(path, source)
        ),
        key=lambda path: (path.relative_to(source).as_posix().lower(), path.relative_to(source).as_posix()),
    )


def _copy_non_clobber(source: Path, target: Path) -> None:
    """Copy a raw original only when the destination does not already exist."""
    with source.open("rb") as source_handle:
        descriptor, staging_name = tempfile.mkstemp(
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".staging",
        )
        staging = Path(staging_name)
        published = False
        try:
            with os.fdopen(descriptor, "wb") as staging_handle:
                shutil.copyfileobj(source_handle, staging_handle)
                staging_handle.flush()
                os.fsync(staging_handle.fileno())
            try:
                os.link(staging, target)
            except FileExistsError as error:
                raise LibraryBusyError(
                    f"Raw destination changed during intake: {target}"
                ) from error
            except BaseException:
                try:
                    published = target.samefile(staging)
                except OSError:
                    published = False
                raise
            else:
                published = True
            _unlink_owned_file(staging)
            shutil.copystat(source, target)
        except BaseException:
            if published:
                _unlink_owned_file(target)
            _unlink_owned_file(staging)
            raise


def _unlink_owned_file(path: Path) -> None:
    """Remove an operation-owned file, clearing a Windows read-only bit if needed."""
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        path.chmod(stat.S_IREAD | stat.S_IWRITE)
        path.unlink(missing_ok=True)


def _intake_assets_locked(
    library_root: Path,
    project_id: str,
    source_path: Path | None,
) -> dict:
    _initialize_library(library_root)
    if source_path is None:
        inbox_root = _library_path(library_root, "inbox")
        source_path = _library_path(library_root, Path("inbox") / project_id)
        if source_path.resolve(strict=False).parent != inbox_root.resolve(strict=False):
            raise ValueError("project_id must resolve to exactly one inbox directory")
        source_path.mkdir(parents=True, exist_ok=True)

    raw_root = _library_path(library_root, "raw")
    existing_hashes = {}
    for path in _raw_files(library_root):
        existing_hashes.setdefault(sha256_file(path), path)

    imported = []
    duplicates = []
    ignored = []
    for candidate in _visible_files(source_path):
        suffix = candidate.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            ignored.append(
                {"sourcePath": str(candidate), "reason": "unsupported_media_type"}
            )
            continue
        digest = sha256_file(candidate)
        asset_id = f"asset-{digest[:16]}"
        if digest in existing_hashes:
            existing = existing_hashes[digest]
            duplicates.append(
                {
                    "id": asset_id,
                    "sourcePath": str(candidate),
                    "existingPath": existing.relative_to(library_root).as_posix(),
                    "sha256": digest,
                }
            )
            continue

        category = category_for_path(candidate.relative_to(source_path))
        target = _destination(raw_root, category, candidate, digest)
        target = _library_path(library_root, target.relative_to(library_root))
        if target.exists() and sha256_file(target) == digest:
            existing_hashes[digest] = target
            duplicates.append(
                {
                    "id": asset_id,
                    "sourcePath": str(candidate),
                    "existingPath": target.relative_to(library_root).as_posix(),
                    "sha256": digest,
                }
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        _copy_non_clobber(candidate, target)
        existing_hashes[digest] = target
        imported.append(
            {
                "id": asset_id,
                "sourcePath": str(candidate),
                "path": target.relative_to(library_root).as_posix(),
                "kind": STORAGE_KINDS[category],
                "sha256": digest,
            }
        )

    _rebuild_catalog(library_root)
    instant, updated_at = _utc_now()
    summary = {
        "libraryRoot": str(library_root),
        "projectId": project_id,
        "source": str(source_path),
        "updatedAt": updated_at,
        "importedCount": len(imported),
        "duplicateCount": len(duplicates),
        "ignoredCount": len(ignored),
        "imported": imported,
        "duplicates": duplicates,
        "ignored": ignored,
    }
    _write_library_json(library_root, "catalog/intake_log.json", summary)
    timestamp = instant.strftime("%Y%m%dT%H%M%S%fZ")
    _write_library_json(
        library_root,
        Path("catalog/intake_logs") / f"{timestamp}-{_safe_project_id(project_id)}.json",
        summary,
    )
    return summary


def intake_assets(library_root: Path, project_id: str, source: Path | None = None) -> dict:
    """Copy supported originals, rebuild catalogs, and return an intake summary."""
    library_root = library_root.expanduser().resolve()
    source_path = None
    if source is None:
        _validate_default_project_id(project_id)
    else:
        source_path = source.expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Explicit source does not exist: {source_path}")
        if not source_path.is_dir():
            raise NotADirectoryError(f"Explicit source is not a directory: {source_path}")
    with _library_lock(library_root):
        return _intake_assets_locked(library_root, project_id, source_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Intake media into a shared asset library")
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    try:
        result = intake_assets(args.library_root, args.project_id, args.source)
    except (LibraryBusyError, OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
