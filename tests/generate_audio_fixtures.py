"""Regenerate the compact MP3, FLAC, and Ogg Vorbis test fixtures.

This developer utility requires FFmpeg. The generated fixture bytes are checked in,
so neither FFmpeg nor an audio encoder is needed when building or testing a wheel.
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


DATA_DIRECTORY = Path(__file__).parent / "data"
ENCODERS = {
    "tiny-mp3.mp3.b64": ["-codec:a", "libmp3lame", "-b:a", "128k"],
    "tiny-flac.flac.b64": ["-codec:a", "flac"],
    "tiny-vorbis.ogg.b64": ["-codec:a", "libvorbis", "-q:a", "3"],
}


def write_source_wave(path: Path) -> None:
    frame_count = 4_800
    frames = bytearray(frame_count * 2)
    frames[:2] = (1_000).to_bytes(2, byteorder="little", signed=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48_000)
        output.writeframes(frames)


def main() -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("FFmpeg is required to regenerate the audio fixtures")

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        source_path = temporary_path / "source.wav"
        write_source_wave(source_path)

        for fixture_name, encoder_arguments in ENCODERS.items():
            audio_suffix = ".".join(fixture_name.split(".")[1:-1])
            audio_path = temporary_path / f"fixture.{audio_suffix}"
            subprocess.run(
                [
                    ffmpeg,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source_path),
                    "-map_metadata",
                    "-1",
                    *encoder_arguments,
                    str(audio_path),
                ],
                check=True,
            )
            encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
            wrapped = "\n".join(
                encoded[offset : offset + 76]
                for offset in range(0, len(encoded), 76)
            )
            (DATA_DIRECTORY / fixture_name).write_text(
                f"{wrapped}\n", encoding="ascii"
            )


if __name__ == "__main__":
    main()
