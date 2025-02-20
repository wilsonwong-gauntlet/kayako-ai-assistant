"""Voice processing using OpenAI's Whisper and TTS APIs."""

import os
import tempfile
from typing import AsyncGenerator, BinaryIO, Optional, Union, List
from pathlib import Path
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import numpy as np
import logging
from io import BytesIO
from . import config

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logger = logging.getLogger(__name__)

class AudioBuffer:
    """Manages streaming audio data."""
    
    def __init__(self, max_size: int = 1024 * 1024):  # 1MB default
        self.buffer = BytesIO()
        self.max_size = max_size
        self.current_size = 0
        
    def add_chunk(self, chunk: bytes) -> bool:
        """
        Add an audio chunk to the buffer.
        
        Returns:
            bool: True if buffer is full and ready for processing
        """
        chunk_size = len(chunk)
        
        # Check if adding this chunk would exceed max size
        if self.current_size + chunk_size > self.max_size:
            return True
            
        self.buffer.write(chunk)
        self.current_size += chunk_size
        return False
        
    def get_audio(self) -> bytes:
        """Get the accumulated audio data."""
        return self.buffer.getvalue()
        
    def clear(self):
        """Clear the buffer."""
        self.buffer = BytesIO()
        self.current_size = 0

async def stream_transcription(audio_buffer: AudioBuffer) -> AsyncGenerator[str, None]:
    """
    Stream transcription results from audio buffer.
    
    Args:
        audio_buffer: Buffer containing audio data
        
    Yields:
        Transcribed text segments
    """
    try:
        # Create temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            # Write buffer to file
            temp_file.write(audio_buffer.get_audio())
            temp_file.flush()
            
            # Get transcription
            response = await asyncio.to_thread(
                client.audio.transcriptions.create,
                file=temp_file,
                model=config.WHISPER_MODEL,
                language=config.WHISPER_LANGUAGE,
                temperature=config.WHISPER_TEMPERATURE,
                response_format=config.WHISPER_RESPONSE_FORMAT
            )
            
            yield response
            
    except Exception as e:
        logger.error(f"Error in stream_transcription: {str(e)}")
        yield ""

async def transcribe_audio(
    audio_data: Union[str, Path, BinaryIO, bytes],
    prompt: Optional[str] = None
) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Args:
        audio_data: Audio file path, file-like object, or bytes
        prompt: Optional prompt to guide transcription
    
    Returns:
        Transcribed text
    """
    try:
        # Handle different input types
        if isinstance(audio_data, (str, Path)):
            with open(audio_data, 'rb') as audio_file:
                response = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    file=audio_file,
                    model=config.WHISPER_MODEL,
                    language=config.WHISPER_LANGUAGE,
                    temperature=config.WHISPER_TEMPERATURE,
                    response_format=config.WHISPER_RESPONSE_FORMAT,
                    prompt=prompt
                )
        elif isinstance(audio_data, bytes):
            # Create temporary file for bytes
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                response = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    file=temp_file,
                    model=config.WHISPER_MODEL,
                    language=config.WHISPER_LANGUAGE,
                    temperature=config.WHISPER_TEMPERATURE,
                    response_format=config.WHISPER_RESPONSE_FORMAT,
                    prompt=prompt
                )
        else:
            # audio_data is already a file-like object
            response = await asyncio.to_thread(
                client.audio.transcriptions.create,
                file=audio_data,
                model=config.WHISPER_MODEL,
                language=config.WHISPER_LANGUAGE,
                temperature=config.WHISPER_TEMPERATURE,
                response_format=config.WHISPER_RESPONSE_FORMAT,
                prompt=prompt
            )
        return response

    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return ""

async def text_to_speech(
    text: str,
    voice: str = config.TTS_VOICE,
    speed: float = config.TTS_SPEED
) -> bytes:
    """
    Convert text to speech using OpenAI's TTS API.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use (e.g., alloy, echo, fable)
        speed: Speaking speed multiplier
    
    Returns:
        Audio data as bytes
    """
    try:
        response = await asyncio.to_thread(
            client.audio.speech.create,
            model=config.TTS_MODEL,
            voice=voice,
            input=text,
            speed=speed
        )
        
        # Get the audio content
        audio_data = response.content
        return audio_data

    except Exception as e:
        logger.error(f"Error converting text to speech: {str(e)}")
        return b"" 