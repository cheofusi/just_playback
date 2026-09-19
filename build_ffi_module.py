import json
import os
import platform
from pathlib import Path

from cffi import FFI
ffibuilder = FFI()

ma_defs_path = Path.cwd() / 'just_playback' / 'ma_defs.txt'
with ma_defs_path.open(mode='r') as f:
    ma_defs = f.read()

miniaudio_src = str(Path("just_playback", "miniaudio", "miniaudio.c"))
stb_vorbis_src = str(Path("just_playback", "miniaudio", "stb_vorbis.c"))
ma_playback_src = str(Path("just_playback", "ma_playback.c"))
include_dir = str(Path('just_playback'))

libraries = []
compiler_args = []
sources = [miniaudio_src, stb_vorbis_src, ma_playback_src]
include_dirs = [include_dir]
extra_objects = []
depends = [str(Path("just_playback", "ma_atomic_bridge.h"))]
define_macros = [("MA_NO_GENERATION", "1")]

if os.name == "posix":
    libraries = ["dl", "m", "pthread"]
    compiler_args = ["-g1", "-O3"]

default_opus_config = Path.cwd() / "build" / "native" / "opus-build.json"
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
    if opus_config.get("format") != 1:
        raise RuntimeError(f"Unsupported Opus build config format: {opus_config_path}")
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
        str(
            Path(
                "just_playback",
                "miniaudio",
                "extras",
                "decoders",
                "libopus",
                "miniaudio_libopus.c",
            )
        )
    )
    include_dirs.extend(str(path) for path in opus_include_dirs)
    extra_objects.extend(str(path) for path in opus_extra_objects)
    for path in [opus_config_path, *opus_extra_objects]:
        try:
            depends.append(str(path.resolve().relative_to(Path.cwd().resolve())))
        except ValueError:
            depends.append(str(path))
    define_macros.append(("JUST_PLAYBACK_HAS_OPUS", "1"))

ffibuilder.cdef( ma_defs + '\n\n'
                """ 
                    typedef struct {  
                        ma_uint32 num_playback_devices;

                        ma_decoder decoder;
                        ma_device_config deviceConfig;
                        ma_device device;

                        float playback_volume;
                        bool audio_stream_ready;

                        ...;
                    }
                    Attrs;
                    
                    ma_result check_available_playback_devices(Attrs* attrs);
                    void init_attrs(Attrs* attrs);
                    ma_result load_file(Attrs* attrs, const char* path_to_file);
                    ma_result load_file_w(Attrs* attrs, const wchar_t* path_to_file);
                    ma_result probe_file(const char* path_to_file);
                    ma_result probe_file_w(const wchar_t* path_to_file);
                    bool has_opus_support(void);
                    ma_result init_audio_stream(Attrs* attrs);
                    ma_result start_audio_stream(Attrs* attrs);
                    ma_result stop_audio_stream(Attrs* attrs);
                    ma_result terminate_audio_stream(Attrs* attrs);
                    ma_result request_audio_stream_seek(Attrs* attrs, ma_uint64 frame_offset);
                    ma_uint64 get_audio_stream_frame_offset(Attrs* attrs);
                    ma_result set_audio_stream_looping(Attrs* attrs, bool enabled);
                    bool is_audio_stream_looping(Attrs* attrs);
                    bool is_audio_stream_active(Attrs* attrs);
                    bool did_audio_stream_end_naturally(Attrs* attrs);
                    void clear_audio_stream_ended_naturally(Attrs* attrs);
                    void audio_stream_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount);
                    ma_result set_device_volume(Attrs* attrs);
                    ma_result get_device_volume(Attrs* attrs);
                """)

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
