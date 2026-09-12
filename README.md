# just_playback

A small Python library for playing audio files. It provides file-format-independent methods for loading, playing, pausing, resuming, stopping, and seeking audio, as well as inspecting playback position and controlling volume.

The package uses [miniaudio](https://github.com/mackron/miniaudio) for awesome cross-platform, dependency-free asynchronous audio playback that stays away from your main thread.

## Supported audio formats

- WAV
- MP3
- FLAC
- Ogg Vorbis
- Ogg Opus in the official Linux, Windows, and macOS wheels

`just_playback.SUPPORTED_AUDIO_FORMATS` reports the formats enabled in the installed build. Ogg Opus is an optional native component and is not enabled in source builds unless its dependencies have been prepared as described below.

## Requirements

just_playback requires Python 3.9 or newer.

## Installation

```shell
python -m pip install just-playback
```

Pre-built wheels do not require a compiler. Installing from source requires a C compiler and the development headers for your Python installation.

## Usage

``` python
>>> from just_playback import Playback
>>> playback = Playback() # creates an object for managing playback of a single audio file
>>> playback.load_file('music/sample.mp3')
# or just pass the filename directly to the constructor

>>> playback.play() # plays loaded audio file from the beginning
>>> playback.pause() # pauses playback. No effect if playback is already paused
>>> playback.resume() # resumes playback. No effect if playback is playing
>>> playback.stop() # stops playback. No effect if playback is not active

>>> playback.seek(60) # positions playback at 1 minute from the start of the audio file. No effect
# if playback is not active
>>> playback.set_volume(0.5) # sets the playback volume to 50% of the audio file's original value

>>> playback.loop_at_end(True) # since 0.1.5. Causes playback to automatically restart when it completes.

>>> playback.active # True if playback is active i.e playing or paused
>>> playback.playing # True if playback is active and not paused
>>> playback.curr_pos # current absolute playback position in seconds from 
				  #	the start of the audio file (unlike pygame.mixer.get_pos). 
>>> playback.paused # True if playback is paused.
>>> playback.duration # length of the audio file in seconds. 
>>> playback.volume # current playback volume
>>> playback.loops_at_end # True if playback is set to restart when it completes.
```

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then create and synchronize the project environment:

```shell
uv sync
```

To build with Ogg Opus support, first download the pinned Xiph release archives, verify their checksums, and build the static dependencies:

```shell
python tools/prepare_opus_deps.py
uv build --wheel
```

The downloaded sources and compiled libraries are stored under the ignored `build/native` directory. A normal source build that does not run this preparation step remains dependency-free and excludes Ogg Opus support.

The release-wheel jobs run that preparation automatically. They statically link libogg, libopus, and opusfile into the extension, so wheel users do not need separate codec DLLs, dylibs, or shared libraries. CMake and network access are only required when preparing a source build with Opus enabled.

Build the source distribution:

```shell
uv build --sdist
```
