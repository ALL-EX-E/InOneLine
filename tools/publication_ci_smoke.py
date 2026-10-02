from __future__ import annotations

import json
import tempfile
from pathlib import Path

from release_publication import ManifestError, file_sha256, load_manifest, stage_assets, verify_directory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = PROJECT_ROOT / ".github" / "workflows"


def expect_manifest_error(fn, label: str) -> None:
    try:
        fn()
    except ManifestError:
        return
    raise AssertionError(f"Expected ManifestError: {label}")


def main() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        notes = root / "RELEASE_NOTES_1.2.3.md"
        notes.write_text("# Test release\n", encoding="utf-8")

        accepted = root / "accepted"
        accepted.mkdir()
        (accepted / "installer.exe").write_bytes(b"installer-bytes")
        (accepted / "source.zip").write_bytes(b"source-bytes")

        manifest_data = {
            "schema": 1,
            "release_tag": "v1.2.3-maintenance-2026-10-02",
            "release_title": "InOneLine 1.2.3 Maintenance",
            "release_notes": notes.name,
            "accepted_artifact_id": 123456,
            "accepted_target_commit": "a" * 40,
            "assets": [
                {
                    "artifact_path": "installer.exe",
                    "release_name": "InOneLine_Setup_1.2.3.exe",
                    "sha256": file_sha256(accepted / "installer.exe"),
                },
                {
                    "artifact_path": "source.zip",
                    "release_name": "InOneLine_Source_1.2.3.zip",
                    "sha256": file_sha256(accepted / "source.zip"),
                },
            ],
        }
        manifest_path = root / "request.json"
        manifest_path.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

        manifest = load_manifest(manifest_path, root)
        staged = root / "staged"
        stage_assets(manifest, accepted, staged)
        verify_directory(manifest, staged)

        (accepted / "installer.exe").write_bytes(b"tampered")
        expect_manifest_error(lambda: stage_assets(manifest, accepted, root / "tampered-stage"), "tampered accepted bytes")

        bad = dict(manifest_data)
        bad["release_notes"] = "../escape.md"
        bad_path = root / "bad-traversal.json"
        bad_path.write_text(json.dumps(bad), encoding="utf-8")
        expect_manifest_error(lambda: load_manifest(bad_path, root), "release-notes traversal")

        duplicate = json.loads(json.dumps(manifest_data))
        duplicate["assets"][1]["release_name"] = duplicate["assets"][0]["release_name"]
        duplicate_path = root / "bad-duplicate.json"
        duplicate_path.write_text(json.dumps(duplicate), encoding="utf-8")
        expect_manifest_error(lambda: load_manifest(duplicate_path, root), "duplicate release asset name")

    generic = WORKFLOWS / "publish-accepted-release.yml"
    assert generic.is_file(), "Generic accepted-release publisher is missing"
    workflow = generic.read_text(encoding="utf-8")
    assert ".github/release/requests/*.json" in workflow
    assert "workflow_dispatch:" in workflow
    assert "git diff --name-status" in workflow
    assert 'if ($status -ne "A")' in workflow
    assert "gh release view" in workflow
    assert "git ls-remote --exit-code --tags" in workflow
    assert "release_publication.py stage" in workflow
    assert "release_publication.py verify-dir" in workflow
    assert "RELEASE_NOTES_1.0.4.md" not in workflow

    for version in ("1.0.4", "1.0.5", "1.0.6", "1.0.7", "1.0.8"):
        assert not (WORKFLOWS / f"publish-{version}.yml").exists(), f"Historical publisher still active: {version}"
        assert (PROJECT_ROOT / f"RELEASE_NOTES_{version}.md").is_file(), f"Historical release notes missing: {version}"

    print("PUBLICATION_CI_CONSOLIDATION=PASS")


if __name__ == "__main__":
    main()
