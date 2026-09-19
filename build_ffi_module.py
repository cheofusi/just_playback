import json
import os
import platform
from pathlib import Path

from cffi import FFI
ffibuilder = FFI()

PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = PROJECT_ROOT / "just_playback"


def project_path(path: Path) -> str:
    """Return a setuptools-compatible path relative to the project root."""

    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


ma_defs_path = PACKAGE_ROOT / "ma_defs.txt"
with ma_defs_path.open(mode="r", encoding="utf-8") as f:
    ma_defs = f.read()
ma_playback_api_path = PACKAGE_ROOT / "ma_playback_api.h"
with ma_playback_api_path.open(mode="r", encoding="utf-8") as f:
    ma_playback_api = f.read()

miniaudio_src = project_path(PACKAGE_ROOT / "miniaudio" / "miniaudio.c")
stb_vorbis_src = project_path(PACKAGE_ROOT / "miniaudio" / "stb_vorbis.c")
ma_playback_src = project_path(PACKAGE_ROOT / "ma_playback.c")
include_dir = project_path(PACKAGE_ROOT)

libraries = []
compiler_args = []
sources = [miniaudio_src, stb_vorbis_src, ma_playback_src]
include_dirs = [include_dir]
extra_objects = []
depends = [
    project_path(PACKAGE_ROOT / "ma_atomic_bridge.h"),
    project_path(ma_playback_api_path),
]
define_macros = [("MA_NO_GENERATION", "1")]

if os.name == "posix":
    libraries = ["dl", "m", "pthread"]
    compiler_args = ["-g1", "-O3"]

default_opus_config = PROJECT_ROOT / "build" / "native" / "opus-build.json"
opus_manifest_path = PROJECT_ROOT / "native" / "opus-deps.json"
opus_config_env = os.environ.get("JUST_PLAYBACK_OPUS_CONFIG")
opus_config_path = Path(opus_config_env).resolve() if opus_config_env else default_opus_config

if opus_config_env and not opus_config_path.is_file():
    raise RuntimeError(
        f"JUST_PLAYBACK_OPUS_CONFIG does not name a file: {opus_config_path}"
    )
if os.environ.get("CIBUILDWHEEL") == "1" and not opus_config_path.is_file():
    raise RuntimeError(
        "cibuildwheel requires prepared Ogg Opus dependencies; "
        "the platform before-all step did not create "
        f"{opus_config_path}"
    )

if opus_config_path.is_file():
    opus_config = json.loads(opus_config_path.read_text(encoding="utf-8"))
    if opus_config.get("format") != 2:
        raise RuntimeError(
            f"Stale or unsupported Opus build config: {opus_config_path}. "
            "Run tools/prepare_opus_deps.py again."
        )

    opus_manifest = json.loads(opus_manifest_path.read_text(encoding="utf-8"))
    expected_dependencies = {
        dependency["name"]: {
            "version": dependency["version"],
            "sha256": dependency["sha256"],
        }
        for dependency in opus_manifest["dependencies"]
    }
    if opus_config.get("dependencies") != expected_dependencies:
        raise RuntimeError(
            f"Prepared Opus dependencies in {opus_config_path} do not match "
            f"{opus_manifest_path}. Run tools/prepare_opus_deps.py again."
        )
    if opus_config.get("platform") != platform.system():
        raise RuntimeError(
            f"Opus dependencies in {opus_config_path} were built for "
            f"{opus_config.get('platform')}, not {platform.system()}"
        )
    machine_aliases = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    configured_machine = machine_aliases.get(
        opus_config.get("machine", "").lower(), opus_config.get("machine", "").lower()
    )
    build_machine = machine_aliases.get(platform.machine().lower(), platform.machine().lower())
    if configured_machine != build_machine:
        raise RuntimeError(
            f"Opus dependencies in {opus_config_path} were built for "
            f"{opus_config.get('machine')}, not {platform.machine()}"
        )

    opus_include_dirs = [Path(path) for path in opus_config["include_dirs"]]
    opus_extra_objects = [Path(path) for path in opus_config["extra_objects"]]
    missing_paths = [
        path for path in [*opus_include_dirs, *opus_extra_objects] if not path.exists()
    ]
    if missing_paths:
        raise RuntimeError(
            "The prepared Opus build is incomplete; missing: "
            + ", ".join(str(path) for path in missing_paths)
        )

    sources.append(
        project_path(
            PACKAGE_ROOT
            / "miniaudio"
            / "extras"
            / "decoders"
            / "libopus"
            / "miniaudio_libopus.c"
        )
    )
    include_dirs.extend(str(path) for path in opus_include_dirs)
    extra_objects.extend(str(path) for path in opus_extra_objects)
    for path in [opus_manifest_path, opus_config_path, *opus_extra_objects]:
        try:
            depends.append(project_path(path))
        except ValueError:
            depends.append(str(path.resolve()))
    define_macros.append(("JUST_PLAYBACK_HAS_OPUS", "1"))

attrs_cdef = """
    typedef struct {
        ma_uint32 num_playback_devices;

        ma_decoder decoder;
        ma_device_config deviceConfig;
        ma_device device;

        float playback_volume;

        ...;
    }
    Attrs;
"""

ffibuilder.cdef("\n\n".join((ma_defs, attrs_cdef, ma_playback_api)))

ffibuilder.set_source("_ma_playback",  
            """ 
                    #include "ma_playback.h"
            """,
            sources=sources,
            include_dirs=include_dirs,
            libraries=libraries,
            extra_objects=extra_objects,
            depends=depends,
            extra_compile_args=compiler_args,
            define_macros=define_macros,
            )    

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
