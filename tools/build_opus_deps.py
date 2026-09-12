#!/usr/bin/env python3
"""Build pinned Ogg Opus dependencies as static libraries."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_ROOT = PROJECT_ROOT / "build" / "native"


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def find_static_library(prefix: Path, names: tuple[str, ...]) -> Path:
    matches = [path for name in names for path in prefix.rglob(name)]
    if len(matches) != 1:
        rendered = ", ".join(str(path) for path in matches) or "none"
        raise RuntimeError(f"Expected one of {names!r} below {prefix}; found {rendered}")
    return matches[0].resolve()


def build(build_root: Path) -> Path:
    sources = build_root / "sources"
    for dependency in ("ogg", "opus", "opusfile"):
        if not (sources / dependency).is_dir():
            raise RuntimeError(
                f"Missing {dependency} sources. Run tools/fetch_opus_deps.py first."
            )

    cmake_build = build_root / "cmake"
    prefix = (build_root / "prefix").resolve()
    config_path = build_root / "opus-build.json"
    if cmake_build.exists():
        shutil.rmtree(cmake_build)
    if prefix.exists():
        shutil.rmtree(prefix)

    # Cache values can be embedded verbatim in generated CMake scripts. Forward
    # slashes prevent Windows paths such as ``D:\a`` from becoming escapes.
    configure = [
        "cmake",
        "-S",
        str(PROJECT_ROOT / "native" / "opus"),
        "-B",
        str(cmake_build),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_LIBDIR=lib",
        f"-DCMAKE_INSTALL_PREFIX={prefix.as_posix()}",
        f"-DJUST_PLAYBACK_OPUS_SOURCE_DIR={sources.resolve().as_posix()}",
    ]
    if os.name == "nt":
        configure.append("-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL")
    deployment_target = os.environ.get("MACOSX_DEPLOYMENT_TARGET")
    if platform.system() == "Darwin" and not deployment_target:
        deployment_target = "11.0" if platform.machine() == "arm64" else "10.9"
    if deployment_target:
        configure.append(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={deployment_target}")

    run(configure)
    run(["cmake", "--build", str(cmake_build), "--config", "Release", "--parallel"])
    run(["cmake", "--install", str(cmake_build), "--config", "Release"])

    suffixes = (".lib",) if os.name == "nt" else (".a",)
    libraries = [
        find_static_library(prefix, tuple(f"*opusfile{suffix}" for suffix in suffixes)),
        find_static_library(prefix, tuple(f"*opus{suffix}" for suffix in suffixes)),
        find_static_library(prefix, tuple(f"*ogg{suffix}" for suffix in suffixes)),
    ]
    config = {
        "format": 1,
        "platform": platform.system(),
        "machine": platform.machine(),
        "include_dirs": [
            str((prefix / "include").resolve()),
            str((prefix / "include" / "opus").resolve()),
        ],
        "extra_objects": [str(library) for library in libraries],
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {config_path}")
    return config_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-root", type=Path, default=DEFAULT_BUILD_ROOT)
    args = parser.parse_args()
    build(args.build_root.resolve())


if __name__ == "__main__":
    main()
