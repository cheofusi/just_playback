import pathlib
import math
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from typing import Optional, Any

from tinytag import TinyTag
from _ma_playback import ffi, lib
from .ma_errs import MA_ERRORS


class Playback:
    """
        A class for controlling playback of a single audio file in a way that's independent of the audio
        file's format. Works for all file formats supported by https://github.com/mackron/miniaudio.
    """
    
    def __init__(self, path_to_file: Optional[str] = ''):
        if not lib.check_devices():
            logging.critical('No device is available for playback!!')
        
        else:
            self.__ma_attrs = ffi.new("Attrs *")
            lib.init_attrs(self.__ma_attrs)
            
            self.__paused: bool = False
            self.__file_duration: float = 0.0
            self.__playback_volume: float = 1.0

            if path_to_file:
                self.load_file(path_to_file)   
    
    def load_file(self, path_to_file: str) -> bool:
        """
            Loads an audio file using one of the available backends.
            This also kills any active playback

        Args:
            path_to_file: The absolute or relative path to the audio file

        Returns True if the audio file was successfully loaded and False otherwise
        """

        audio_file = pathlib.Path(path_to_file)
        if not audio_file.exists() or not path_to_file:
            logging.error('Audio file not found.')
            return False
        
        self.__log_possible_error(lib.terminate_audio_stream(self.__ma_attrs))

        if not lib.load_file(self.__ma_attrs, path_to_file.encode('utf-8')):
            logging.error('Failed to load ' + path_to_file)
            self.__log_possible_error(False)
            return False

        self.__log_possible_error(lib.init_audio_stream(self.__ma_attrs))
        self.__log_possible_error(lib.set_device_volume(self.__ma_attrs, self.__playback_volume))
        self.__file_duration = TinyTag.get(path_to_file).duration

    def play(self) -> None:
        """
            Plays the loaded file from the beginning. Ignores the fact
            that the current playback might be paused. Has no effect if no 
            audio file has been loaded
        """

        if not self.__ma_attrs.audio_stream_ready:
            logging.error('No audio file has been loaded yet!!')
            return
        
        self.stop()
        self.__log_possible_error(lib.start_audio_stream(self.__ma_attrs))

    def stop(self) -> None:
        """
            Stops audio playback. Has no effect if playback is inactive
        """

        if self.active:
            if not self.__paused:
                self.__log_possible_error(lib.stop_audio_stream(self.__ma_attrs))
            self.__ma_attrs.frame_offset = 0
            self.__ma_attrs.user_seeked = True
            self.__paused = False
    
    def pause(self) -> None:
        """
            Pauses audio playback. Has no effect if playback is inactive or is
            already paused
        """

        if self.active and not self.__paused:
            self.__log_possible_error(lib.stop_audio_stream(self.__ma_attrs))
            self.__paused = True

    def resume(self) -> None:
        """ 
            Resumes audio playback. Has no effect if playback is inactive or is 
            not paused
        """

        if self.active and self.__paused:
            self.__paused = False
            self.__log_possible_error(lib.start_audio_stream(self.__ma_attrs))
    
    def seek(self, pos: float) -> None:
        """
            Moves playback to a specified position. Has no effect if playback is
            inactive
        
        Args:
            pos: position in seconds for playback to jump to. It's value is clamped
                 to the interval [0, self.duration].
        """

        if self.active:
            pos = min(max(pos, 0), self.__file_duration)
            self.__ma_attrs.frame_offset = math.floor(pos * self.__ma_attrs.sample_rate)
            self.__ma_attrs.user_seeked = True
    
    def set_volume(self, volume: float) -> None:
        """
            Sets the volume for the playback device
        Args:
            volume: A value in the interval [0, 1].
        """

        self.__playback_volume = min(max(volume, 0), 1)
        if self.active:
            self.__log_possible_error(lib.set_device_volume(self.__ma_attrs, volume))
    
    @property
    def active(self) -> bool:
        """
            Returns True if playback is playing or is paused and False otherwise
        """
    
        if not self.__ma_attrs.audio_stream_ready:
            return False

        return self.__ma_attrs.playback_active or self.__paused

    @property
    def curr_pos(self) -> float:
        """
            Returns playback's current position or offset in seconds from the
            beginning of audio file.
        """

        if self.active:
            pos = self.__ma_attrs.frame_offset / self.__ma_attrs.sample_rate
            return pos 
        
        return 0
    
    @property
    def paused(self) -> bool:
        return self.__paused
    
    @property
    def duration(self) -> float:
        return self.__ma_attrs.duration
    
    @property
    def volume(self) -> float:
        """
            Returns playback's current volume, a value in the interval [0, 1]
        """

        if self.active:
            volume = lib.get_device_volume(self.__ma_attrs)
            if volume == -1:
                self.__log_possible_error(False)

            else:
                self.__playback_volume = volume
            
        return self.__playback_volume

    def __log_possible_error(self, result: bool) -> None:
        """ 
            Internal method for error logging. DO NOT CALL
        """

        if not result:
            logging.debug('Miniaudio says: {}'.format(MA_ERRORS[self.__ma_attrs.op_errcode]))

    def __del__(self):
        self.__log_possible_error(lib.terminate_audio_stream(self.__ma_attrs))