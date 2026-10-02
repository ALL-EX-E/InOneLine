from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9][A-Za-z0-9._-]*)?$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class ManifestError(ValueError):
    pass


def _safe_repo_path(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text or "\\" in text:
        raise ManifestError(f"{field} must be a non-empty relative path using forward slashes")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ManifestError(f"{field} must not be absolute or contain traversal")
    return path.as_posix()


def _safe_release_name(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text or "/" in text or "\\" in text or text in (".", ".."):
        raise ManifestError(f"{field} must be a single file name")
    return text


def _sha256(value: Any, field: str) -> str:
    text = str(value or "").strip().lower()
    if not SHA_RE.fullmatch(text):
        raise ManifestError(f"{field} must be a 64-character SHA-256 hex string")
    return text


def load_manifest(path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ManifestError(f"Cannot read publication manifest: {exc}") from exc

    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be a JSON object")
    if data.get("schema") != 1:
        raise ManifestError("Unsupported publication manifest schema; expected 1")

    tag = str(data.get("release_tag") or "").strip()
    if not TAG_RE.fullmatch(tag):
        raise ManifestError("release_tag must be an InOneLine version tag such as v1.0.9 or v1.0.8-maintenance-2026-10-01")

    title = str(data.get("release_title") or "").strip()
    if not title or "\n" in title or "\r" in title or len(title) > 200:
        raise ManifestError("release_title must be one non-empty line of at most 200 characters")

    notes = _safe_repo_path(data.get("release_notes"), "release_notes")
    if not notes.lower().endswith(".md"):
        raise ManifestError("release_notes must point to a Markdown file")

    try:
        artifact_id = int(data.get("accepted_artifact_id"))
    except Exception as exc:
        raise ManifestError("accepted_artifact_id must be a positive integer") from exc
    if artifact_id <= 0:
        raise ManifestError("accepted_artifact_id must be a positive integer")

    target = str(data.get("accepted_target_commit") or "").strip().lower()
    if not COMMIT_RE.fullmatch(target):
        raise ManifestError("accepted_target_commit must be a full 40-character commit SHA")

    assets = data.get("assets")
    if not isinstance(assets, list) or not 2 <= len(assets) <= 8:
        raise ManifestError("assets must contain between 2 and 8 accepted files")

    normalized_assets: list[dict[str, str]] = []
    artifact_paths: set[str] = set()
    release_names: set[str] = set()

    for index, raw in enumerate(assets):
        if not isinstance(raw, dict):
            raise ManifestError(f"assets[{index}] must be an object")
        artifact_path = _safe_repo_path(raw.get("artifact_path"), f"assets[{index}].artifact_path")
        release_name = _safe_release_name(raw.get("release_name"), f"assets[{index}].release_name")
        digest = _sha256(raw.get("sha256"), f"assets[{index}].sha256")

        if artifact_path in artifact_paths:
            raise ManifestError(f"Duplicate artifact_path: {artifact_path}")
        if release_name in release_names:
            raise ManifestError(f"Duplicate release_name: {release_name}")
        artifact_paths.add(artifact_path)
        release_names.add(release_name)
        normalized_assets.append({
            "artifact_path": artifact_path,
            "release_name": release_name,
            "sha256": digest,
        })

    normalized = {
        "schema": 1,
        "release_tag": tag,
        "release_title": title,
        "release_notes": notes,
        "accepted_artifact_id": artifact_id,
        "accepted_target_commit": target,
        "assets": normalized_assets,
    }

    if repo_root is not None:
        notes_path = (repo_root / Path(*PurePosixPath(notes).parts)).resolve()
        root = repo_root.resolve()
        try:
            notes_path.relative_to(root)
        except ValueError as exc:
            raise ManifestError("release_notes escaped repository root") from exc
        if not notes_path.is_file():
            raise ManifestError(f"Release notes file does not exist: {notes}")

    return normalized


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_under(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / Path(*PurePosixPath(relative).parts)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ManifestError(f"Path escaped accepted artifact root: {relative}") from exc
    return path


def stage_assets(manifest: dict[str, Any], artifact_root: Path, output_dir: Path) -> None:
    artifact_root = artifact_root.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for asset in manifest["assets"]:
        source = _resolve_under(artifact_root, asset["artifact_path"])
        if not source.is_file():
            raise ManifestError(f"Accepted artifact file is missing: {asset['artifact_path']}")
        actual = file_sha256(source)
        if actual != asset["sha256"]:
            raise ManifestError(
                f"SHA-256 mismatch for {asset['artifact_path']}: expected {asset['sha256']}, got {actual}"
            )
        destination = output_dir / asset["release_name"]
        if destination.exists():
            raise ManifestError(f"Publication staging target already exists: {asset['release_name']}")
        shutil.copy2(source, destination)
        if file_sha256(destination) != asset["sha256"]:
            raise ManifestError(f"File changed while staging: {asset['release_name']}")


def verify_directory(manifest: dict[str, Any], directory: Path) -> None:
    expected = {asset["release_name"]: asset["sha256"] for asset in manifest["assets"]}
    actual_files = {item.name for item in directory.iterdir() if item.is_file()}
    if actual_files != set(expected):
        missing = sorted(set(expected) - actual_files)
        extra = sorted(actual_files - set(expected))
        raise ManifestError(f"Published asset set mismatch; missing={missing}, extra={extra}")
    for name, digest in expected.items():
        actual = file_sha256(directory / name)
        if actual != digest:
            raise ManifestError(f"Published SHA-256 mismatch for {name}: expected {digest}, got {actual}")


def write_github_outputs(path: Path, manifest: dict[str, Any]) -> None:
    rows = {
        "accepted_artifact_id": str(manifest["accepted_artifact_id"]),
        "accepted_target_commit": manifest["accepted_target_commit"],
        "release_tag": manifest["release_tag"],
        "release_title": manifest["release_title"],
        "release_notes": manifest["release_notes"],
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for key, value in rows.items():
            handle.write(f"{key}={value}\n")


def command_validate(args: argparse.Namespace) -> None:
    manifest = load_manifest(Path(args.manifest), Path(args.repo_root))
    if args.github_output:
        write_github_outputs(Path(args.github_output), manifest)
    print(f"PUBLICATION_MANIFEST=PASS tag={manifest['release_tag']} assets={len(manifest['assets'])}")


def command_stage(args: argparse.Namespace) -> None:
    manifest = load_manifest(Path(args.manifest))
    stage_assets(manifest, Path(args.artifact_root), Path(args.output_dir))
    print("PUBLICATION_ACCEPTED_BYTES=PASS")


def command_verify(args: argparse.Namespace) -> None:
    manifest = load_manifest(Path(args.manifest))
    verify_directory(manifest, Path(args.directory))
    print("PUBLICATION_RELEASE_BYTES=PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and stage exact accepted InOneLine release bytes")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--repo-root", required=True)
    validate.add_argument("--github-output")
    validate.set_defaults(func=command_validate)
    stage = sub.add_parser("stage")
    stage.add_argument("--manifest", required=True)
    stage.add_argument("--artifact-root", required=True)
    stage.add_argument("--output-dir", required=True)
    stage.set_defaults(func=command_stage)
    verify = sub.add_parser("verify-dir")
    verify.add_argument("--manifest", required=True)
    verify.add_argument("--directory", required=True)
    verify.set_defaults(func=command_verify)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ManifestError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
