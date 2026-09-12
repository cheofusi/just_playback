#!/usr/bin/env python3
"""Fetch, verify and build the optional Ogg Opus wheel dependencies."""

from fetch_opus_deps import DEFAULT_MANIFEST, fetch
from build_opus_deps import DEFAULT_BUILD_ROOT, build


if __name__ == "__main__":
    fetch(DEFAULT_MANIFEST, DEFAULT_BUILD_ROOT)
    build(DEFAULT_BUILD_ROOT)
