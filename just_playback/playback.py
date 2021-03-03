import sys
import pathlib
import logging

from numpy.core.shape_base import _atleast_2d_dispatcher
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
from typing import Optional

import numpy as np
import audioread as ar

try:
    import pyaudio
except ImportError:
    raise ('pyaudio is required for justplayback to work !!')



class Playback:
    """
        A class for controlling playback of a single audio file in a way that's independent of the audio
        file 's format. For the module to work You must have at least one of the backends supported by 
        the https://github.com/sampsyo/audioread package.
    """
    
    def __init__(self, path_to_file: Optional[str] = ''):
        self.__pa = pyaudio.PyAudio()

        self.__audio_samples: np.ndarray = None
        self.__play_buffer: np.ndarray = None
        self.__audio_attrs: dict = {}
        self.__audio_stream: pyaudio.Stream = None
        
        self.__sample_offset: int = 0
        self.__paused: bool = False

        min_sample_val: float = -0x8000
        max_sample_val: float = 0x7FFF
        self.__audio_mul = lambda sample, factor: \
            np.int16(np.floor(np.fmax(np.fmin(sample * factor, max_sample_val), min_sample_val)))
        
        self.__volume: float = 1.0

        backends = ar.available_backends()
        if not backends:
            logging.critical('No backend is available for decoding your audio files!!')

        else:
            backends = tuple(map(lambda x: str(x).split('.')[1], backends))
            logging.info(f'Available backends are: {backends}')
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
        
        try:
            with ar.audio_open(audio_file) as f:
                logging.info(f'Input file: {f.channels} channels at {f.samplerate} Hz; {f.duration:.2f} seconds.')
                logging.info(f"Using backend: {str(type(f).__module__).split('.')[1]}")
                
                self.__audio_attrs['num_channels'] = f.channels 
                self.__audio_attrs['sample_rate'] = f.samplerate
                self.__audio_attrs['duration'] = f.duration

                samples = [np.frombuffer(buf, dtype=np.int16) for buf in f]

            if self.__audio_stream is not None:
                self.__kill_audio_stream()

            self.__audio_samples = np.concatenate(samples)
            self.__play_buffer = np.copy(self.__audio_samples)

            self.__init_audio_stream()
            return True

        except ar.DecodeError:
            logging.error("The audio file could not be decoded by any of the available backends")
            return False

    def play(self) -> None:
        """
            Plays the loaded file from the beginning. Has no effect if no 
            audio file has been loaded
        """

        if self.__audio_samples is None:
            logging.error('No audio file has been loaded yet!!')
            return
        
        self.__sample_offset = 0
        self.stop()
        self.__resume_audio_stream()

    def stop(self) -> None:
        """
            Stops audio playback. Has no effect if playback is inactive
        """

        if self.active:
            self.__halt_audio_stream()
            self.__sample_offset = 0
            self.__paused = False

    def pause(self) -> None:
        """
            Pauses audio playback. Has no effect if playback is inactive or is
            already paused
        """

        if self.active and not self.__paused:
            self.__halt_audio_stream() 
            self.__paused = True

    def resume(self) -> None:
        """ 
            Resumes audio playback. Has no effect if playback is inactive or is 
            not paused
        """

        if self.active and self.__paused:
            self.__paused = False
            self.__resume_audio_stream()
    
    def seek(self, pos: float) -> None:
        """
            Moves playback to a specified position. Has no effect if playback is
            inactive
        
        Args:
            pos: position in seconds for playback to jump to. It's value is clamped
                 to the interval [0, self.duration].
        """

        if self.active:
            pos = min(max(pos, 0), self.duration)
            frame_offset = pos * self.__audio_attrs['sample_rate']
            self.__sample_offset = int(frame_offset * self.__audio_attrs['num_channels'])  
    
    def set_volume(self, volume: float) -> None:
        """
            Sets the playback volume by applying a gain to the audio signal. The decibel range used 
            is [-48db, 0db], corresponding to the input value range of [0, 1]. Has no effect if playback
            is inactive
        
        Args:
            volume: A value in the interval [0, 1].
        """

        if self.active:
            volume = min(max(volume, 0), 1)
            db_gain = -48 + (48 * volume)
            linear_gain = 10 ** (db_gain / 20)
           
            self.__play_buffer = self.__audio_mul(self.__audio_samples, linear_gain)
            self.__volume = volume
    
    def __audio_stream_callback(self, in_data, frame_count, time_info, status):
        """ 
            Internal method for non blocking audio playback. DO NOT CALL
        """

        inc = frame_count * self.__audio_attrs['num_channels']
        out_data = self.__play_buffer[self.__sample_offset:]
        out_data = out_data[:inc]
        self.__sample_offset += inc
        
        return (out_data.tobytes(), pyaudio.paContinue)
    
    def __init_audio_stream(self) -> None:
        """ 
            Internal method for initalizing the audio stream. DO NOT CALL
        """

        self.__audio_stream = self.__pa.open(
            rate=self.__audio_attrs['sample_rate'],
            channels=self.__audio_attrs['num_channels'],
            format=self.__pa.get_format_from_width(2),  
            output=True,     
            start=False,        
            stream_callback=self.__audio_stream_callback
        )

    def __resume_audio_stream(self) -> None:
        """ 
            Internal method for controlling the audio stream. DO NOT CALL
        """

        self.__audio_stream.start_stream()

    def __halt_audio_stream(self) -> None:
        """ 
            Internal method for controlling the audio stream. DO NOT CALL
        """

        self.__audio_stream.stop_stream()

    def __kill_audio_stream(self) -> None:
        """ 
            Internal method for controlling the audio stream. DO NOT CALL
        """

        self.__audio_stream.stop_stream()
        self.__audio_stream.close()
        self.__audio_stream = None

    @property
    def active(self) -> bool:
        """
            Returns True if playback is playing or is paused and False otherwise
        """

        if self.__audio_stream is None:
            return False

        return self.__audio_stream.is_active() or self.__paused

    @property
    def curr_pos(self) -> float:
        """
            Returns playback's current position or offset in seconds from the
            beginning of audio file.
        """

        if self.active:
            frame_offset = self.__sample_offset / self.__audio_attrs['num_channels']
            pos = frame_offset / self.__audio_attrs['sample_rate']
            return pos 
        
        return 0

    @property
    def paused(self) -> bool:
        return self.__paused
    
    @property
    def duration(self) -> float:
        return self.__audio_attrs['duration']
    
    @property
    def volume(self) -> float:
        """
            Returns playback's current volume as a percentage
        """

        return self.__volume * 100
    
    def __del__(self):
        self.__pa.terminate()
    