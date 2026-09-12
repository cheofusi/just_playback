"""Exercise the bundled Ogg Opus decoder without opening an audio device."""

from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path

from _ma_playback import lib
from just_playback import SUPPORTED_AUDIO_FORMATS
from tinytag import TinyTag


fixture = Path(__file__).parent / "data" / "tiny-opus.ogg.b64"
encoded_audio = base64.b64decode(fixture.read_text(encoding="ascii"))

if not lib.has_opus_support():
    raise AssertionError("the release wheel was built without Ogg Opus support")
if "ogg-opus" not in SUPPORTED_AUDIO_FORMATS:
    raise AssertionError("Ogg Opus is missing from SUPPORTED_AUDIO_FORMATS")


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
