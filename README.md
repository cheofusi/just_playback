# just_playback

A small Python library for playing audio files. It provides file-format-independent methods for loading, playing, pausing, resuming, stopping, and seeking audio, as well as inspecting playback position and controlling volume.

The package uses [miniaudio](https://github.com/mackron/miniaudio) for awesome cross-platform, dependency-free asynchronous audio playback that stays away from your main thread.

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

Build the source distribution:

```shell
uv build --sdist
```
