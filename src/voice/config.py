"""Voice integration configuration."""

# Speech-to-Text (Whisper) settings
WHISPER_MODEL = "whisper-1"
WHISPER_LANGUAGE = "en"  # English
WHISPER_TEMPERATURE = 0  # More deterministic
WHISPER_RESPONSE_FORMAT = "text"

# Text-to-Speech settings
TTS_MODEL = "tts-1"  # or "tts-1-hd" for higher quality
TTS_VOICE = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
TTS_SPEED = 1.0  # Normal speed

# Audio settings
AUDIO_FORMAT = "mp3"
SAMPLE_RATE = 24000  # Hz
CHUNK_SIZE = 4096  # bytes

# Streaming settings
MAX_TOKENS_PER_REQUEST = 4096
STREAM_TIMEOUT = 30  # seconds 