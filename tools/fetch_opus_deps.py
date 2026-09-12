#!/usr/bin/env python3
"""Download and verify the native sources used for Ogg Opus wheels."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "native" / "opus-deps.json"
DEFAULT_BUILD_ROOT = PROJECT_ROOT / "build" / "native"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "just_playback-build"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def validate_archive(members: list[tarfile.TarInfo], expected_root: str) -> None:
    for member in members:
        member_path = PurePosixPath(member.name)
        if (
            member_path.is_absolute()
            or not member_path.parts
            or member_path.parts[0] != expected_root
            or ".." in member_path.parts
        ):
            raise RuntimeError(f"Unsafe path in dependency archive: {member.name!r}")
        if member.issym() or member.islnk():
            raise RuntimeError(f"Links are not allowed in dependency archive: {member.name!r}")
        if not member.isfile() and not member.isdir():
            raise RuntimeError(f"Unsupported entry in dependency archive: {member.name!r}")


def extract(archive: Path, destination: Path, expected_root: str) -> None:
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        temporary_path = Path(temporary)
        with tarfile.open(archive, mode="r:*") as source:
            members = source.getmembers()
            validate_archive(members, expected_root)
            if sys.version_info >= (3, 12):
                source.extractall(temporary_path, members=members, filter="data")
            else:
                source.extractall(temporary_path, members=members)

        extracted_root = temporary_path / expected_root
        if not extracted_root.is_dir():
            raise RuntimeError(f"Archive does not contain {expected_root!r}")
        if destination.exists():
            shutil.rmtree(destination)
        extracted_root.replace(destination)


def fetch(manifest_path: Path, build_root: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    downloads = build_root / "downloads"
    sources = build_root / "sources"
    sources.mkdir(parents=True, exist_ok=True)

    for dependency in manifest["dependencies"]:
        archive_name = Path(urlparse(dependency["url"]).path).name
        archive = downloads / archive_name
        expected_hash = dependency["sha256"]

        if not archive.exists() or sha256(archive) != expected_hash:
            partial = archive.with_suffix(archive.suffix + ".part")
            if partial.exists():
                partial.unlink()
            print(f"Downloading {dependency['name']} {dependency['version']}...")
            download(dependency["url"], partial)
            actual_hash = sha256(partial)
            if actual_hash != expected_hash:
                partial.unlink()
                raise RuntimeError(
                    f"SHA-256 mismatch for {dependency['name']}: "
                    f"expected {expected_hash}, got {actual_hash}"
                )
            partial.replace(archive)

        destination = sources / dependency["name"]
        stamp = destination / ".just-playback-source.json"
        expected_stamp = {
            "version": dependency["version"],
            "sha256": expected_hash,
        }
        if stamp.exists():
            try:
                if json.loads(stamp.read_text(encoding="utf-8")) == expected_stamp:
                    continue
            except (OSError, json.JSONDecodeError):
                pass

        print(f"Extracting {dependency['name']} {dependency['version']}...")
        extract(archive, destination, dependency["archive_root"])
        stamp.write_text(json.dumps(expected_stamp, sort_keys=True) + "\n", encoding="utf-8")

    return sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    args = parser.parse_args()
    fetch(args.manifest.resolve(), args.build_root.resolve())


if __name__ == "__main__":
    main()
