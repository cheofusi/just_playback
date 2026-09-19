# Audio test fixtures

These files contain base64-encoded, 0.1-second mono audio fixtures used by
`tests/check_wheel.py`. The signal is silence except for a small impulse in the
first sample. It contains no third-party audio.

The MP3, FLAC, and Ogg Vorbis fixtures can be regenerated with:

```console
python tests/generate_audio_fixtures.py
```

Regeneration requires an FFmpeg build with the `libmp3lame` and `libvorbis`
encoders. The Ogg Opus fixture is generated separately by
`tests/make_opus_fixture.c` using the pinned libogg and libopus build.
