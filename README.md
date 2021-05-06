
just_playback
=========
A small library for playing audio files in python. Provides file format independent methods for loading audio files, playing, pausing, resuming, stopping, seeking, getting the current playback position, and changing the volume.

The package uses [miniaudio](https://github.com/mackron/miniaudio) for awesome cross-platform, dependency-free asynchronous audio playback that stays away from your main thread.

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