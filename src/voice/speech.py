"""Voice processing using OpenAI's Whisper and TTS APIs."""

import os
import tempfile
from typing import AsyncGenerator, BinaryIO, Optional, Union
from pathlib import Path
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from . import config

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(audio_data: Union[str, Path, BinaryIO], prompt: Optional[str] = None) -> str:
    """
    Transcribe audio using OpenAI's Whisper API.
    
    Args:
        audio_data: Audio file path or file-like object
        prompt: Optional prompt to guide transcription (e.g., expected terms)
    
    Returns:
        Transcribed text
    """
    try:
        # If audio_data is a string or Path, open the file
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
        # Log the error and raise a more specific exception
        print(f"Error transcribing audio: {e}")
        raise

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
        print(f"Error converting text to speech: {e}")
        raise

class AudioBuffer:
    """Buffer for handling streaming audio data."""
    
    def __init__(self, chunk_size: int = config.CHUNK_SIZE):
        self.buffer = bytearray()
        self.chunk_size = chunk_size
    
    def add_data(self, data: bytes) -> None:
        """Add data to the buffer."""
        self.buffer.extend(data)
    
    def get_chunk(self) -> Optional[bytes]:
        """Get a chunk of data if available."""
        if len(self.buffer) >= self.chunk_size:
            chunk = bytes(self.buffer[:self.chunk_size])
            self.buffer = self.buffer[self.chunk_size:]
            return chunk
        return None

async def stream_transcription(audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
    """
    Handle streaming transcription for real-time audio.
    
    Args:
        audio_stream: Async generator yielding audio chunks
    
    Yields:
        Transcribed text segments
    """
    buffer = AudioBuffer()
    
    async for chunk in audio_stream:
        buffer.add_data(chunk)
        
        while audio_chunk := buffer.get_chunk():
            # Create a temporary file for the audio chunk
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_file:
                temp_file.write(audio_chunk)
                temp_file.flush()
                
                # Rewind the file for reading
                temp_file.seek(0)
                
                try:
                    transcription = await transcribe_audio(temp_file)
                    if transcription.strip():
                        yield transcription
                except Exception as e:
                    print(f"Error in stream transcription: {e}")
                    continue 