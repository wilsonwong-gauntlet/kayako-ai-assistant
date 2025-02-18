"""Voice processing package for Kayako AI Call Assistant."""

from .speech import (
    transcribe_audio,
    text_to_speech,
    stream_transcription,
    AudioBuffer
)

__all__ = [
    'transcribe_audio',
    'text_to_speech',
    'stream_transcription',
    'AudioBuffer'
] 