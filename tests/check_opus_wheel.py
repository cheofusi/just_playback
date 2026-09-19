"""Exercise native failure handling and Ogg Opus without opening an audio device."""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

from _ma_playback import ffi, lib
from just_playback import SUPPORTED_AUDIO_FORMATS
from tinytag import TinyTag


fixture = Path(__file__).parent / "data" / "tiny-opus.ogg.b64"
encoded_audio = base64.b64decode(fixture.read_text(encoding="ascii"))

if not lib.has_opus_support():
    raise AssertionError("the release wheel was built without Ogg Opus support")
if "ogg-opus" not in SUPPORTED_AUDIO_FORMATS:
    raise AssertionError("Ogg Opus is missing from SUPPORTED_AUDIO_FORMATS")


def check_native_failure_state() -> None:
    attrs = ffi.new("Attrs *")
    lib.init_attrs(attrs)

    attrs.deviceConfig.playback.format = 1
    attrs.deviceConfig.playback.channels = 17
    attrs.deviceConfig.sampleRate = 12345
    initial_config = (
        attrs.deviceConfig.playback.format,
        attrs.deviceConfig.playback.channels,
        attrs.deviceConfig.sampleRate,
    )

    with tempfile.TemporaryDirectory() as temporary:
        missing_path = str(Path(temporary) / "missing-audio")
        if os.name == "nt":
            load_result = lib.load_file_w(attrs, missing_path)
        else:
            load_result = lib.load_file(attrs, os.fsencode(missing_path))

    if load_result == 0:
        raise AssertionError("a missing audio file was accepted")
    if (
        attrs.deviceConfig.playback.format,
        attrs.deviceConfig.playback.channels,
        attrs.deviceConfig.sampleRate,
    ) != initial_config:
        raise AssertionError("failed decoder initialization changed the device config")

    attrs.deviceConfig.playback.channels = 255
    init_result = lib.init_audio_stream(attrs)
    if init_result == 0:
        raise AssertionError("an invalid device configuration was accepted")
    if attrs.audio_stream_ready:
        raise AssertionError("failed device initialization marked the stream ready")

    start_result = lib.start_audio_stream(attrs)
    if start_result == 0:
        raise AssertionError("an uninitialized device was started")
    if attrs.audio_stream_active:
        raise AssertionError("failed device start marked the stream active")

    attrs.audio_stream_active = True
    stop_result = lib.stop_audio_stream(attrs)
    if stop_result == 0:
        raise AssertionError("an uninitialized device was stopped")
    if not attrs.audio_stream_active:
        raise AssertionError("failed device stop changed the active state")

    null_result_checks = {
        "device enumeration": lib.check_available_playback_devices(ffi.NULL),
        "file load": lib.load_file(ffi.NULL, ffi.NULL),
        "wide file load": lib.load_file_w(ffi.NULL, ffi.NULL),
        "file probe": lib.probe_file(ffi.NULL),
        "wide file probe": lib.probe_file_w(ffi.NULL),
        "device initialization": lib.init_audio_stream(ffi.NULL),
        "device start": lib.start_audio_stream(ffi.NULL),
        "device stop": lib.stop_audio_stream(ffi.NULL),
        "stream termination": lib.terminate_audio_stream(ffi.NULL),
        "volume setter": lib.set_device_volume(ffi.NULL),
        "volume getter": lib.get_device_volume(ffi.NULL),
    }
    for operation, result in null_result_checks.items():
        if result == 0:
            raise AssertionError(f"{operation} accepted a null Attrs pointer")

    lib.init_attrs(ffi.NULL)
    lib.audio_stream_callback(ffi.NULL, ffi.NULL, ffi.NULL, 0)


check_native_failure_state()


def probe(path: Path) -> int:
    if os.name == "nt":
        return lib.probe_file_w(str(path))
    return lib.probe_file(os.fsencode(path))


with tempfile.TemporaryDirectory() as temporary:
    audio_path = Path(temporary) / "tiny-音声.opus"
    audio_path.write_bytes(encoded_audio)
    result = probe(audio_path)
    duration = TinyTag.get(audio_path).duration

    invalid_path = Path(temporary) / "invalid.opus"
    invalid_path.write_bytes(b"not an Ogg Opus stream")
    invalid_result = probe(invalid_path)

if result != 0:
    raise AssertionError(f"Ogg Opus decoder probe failed with miniaudio result {result}")
if duration is None or duration <= 0:
    raise AssertionError("TinyTag could not read the Ogg Opus duration")
if invalid_result == 0:
    raise AssertionError("invalid Ogg Opus data was accepted")

print("Ogg Opus decoder probe: OK")
