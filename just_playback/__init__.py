from .playback import Playback
from _ma_playback import lib


SUPPORTED_AUDIO_FORMATS = frozenset(
    {"wav", "mp3", "flac", "ogg-vorbis"}
    | ({"ogg-opus"} if lib.has_opus_support() else set())
)

__all__ = ["Playback", "SUPPORTED_AUDIO_FORMATS"]
