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
SAMPLE_RATE = 48000  # Hz (increased for better quality)
CHUNK_SIZE = 4096  # bytes

# Twilio Audio Configuration
TWILIO_SPEECH_TIMEOUT = "auto"  # 'auto' or number of seconds
TWILIO_SPEECH_MODEL = "enhanced"  # 'default' or 'enhanced'
TWILIO_INPUT_LANGUAGE = "en-US"  # Language for speech recognition
TWILIO_PROFANITY_FILTER = True  # Filter out profanity
TWILIO_INTERIM_SPEECH_RESULTS = False  # Get interim results while speaking
TWILIO_SPEECH_END_THRESHOLD = 1000  # Silence duration to mark end of speech (ms)

# Voice Response Settings
VOICE_NAME = "Polly.Amy-Neural"  # Twilio neural voice
VOICE_LANGUAGE = "en-GB"  # Voice language
VOICE_RATE = "0.9"  # Speaking rate (0.5 to 4.0)

# Streaming settings
MAX_TOKENS_PER_REQUEST = 4096
STREAM_TIMEOUT = 30  # seconds 