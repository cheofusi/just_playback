
just_playback
=========
A small package for playing audio files in python. Provides file format independent methods for loading audio files, playing, pausing, resuming, stopping, seeking, getting the current playback position, and changing the volume.

Any file format that can be decoded with one of the backends supported by [audioread](https://github.com/beetbox/audioread) is good to go. The package uses [pyaudio](https://github.com/jleb/pyaudio) for awesome cross-platform, dependency-free asynchronous audio playback that stays away from your main thread.

Installation
-------------
	pip install just_playback

Usage
-------------
``` python
from just_playback import Playback
playback = Playback() # creates an object for managing playback of a single audio file
playback.load_file('music-files/sample.mp3')
# or just pass the filename directly to the constructor

playback.play() # plays loaded file from the beginning
playback.pause() # pauses playback. Has no effect if playback is already paused
playback.resume() # resumes playback. Has no effect if playback is playing
playback.stop() # stops playback. Has no effect if playback is not active

playback.seek(60) # positions playback at 1 minute from the start of the audio file
playback.set_volume(0.5) # sets the playback volume to 50% of the audio file's original value

playback.active # checks if playback is active i.e playing or paused
playback.curr_pos # returns the current absolute playback position in seconds from 
				  #	the start of the audio file (unlike pygame.mixer.get_pos). 
playback.paused # checks if playback is paused.
playback.duration # returns the length of the audio file in seconds. 
playback.volume # returns current playback volume
```

Note
--------
The official PyAudio 0.2.11 only supports Python 3.6-.  If you insist on using Python 3.7+, then;

 - On Debian and Ubuntu you'll have to first install the `portaudio19-dev` dev files. See [this](https://stackoverflow.com/a/54396790/8925535).
 - On Windows you'll have to pick a wheel that suits your Python version. See [this](https://stackoverflow.com/a/55630212/8925535)

For Mac users, regardless of thy Python version, first run `brew install portaudio`