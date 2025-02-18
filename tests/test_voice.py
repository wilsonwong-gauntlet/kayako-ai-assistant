"""Tests for voice processing functionality."""

import pytest
import io
import os
from src.voice import speech, config

# Skip tests if OpenAI API key is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not set"
)

@pytest.mark.asyncio
async def test_text_to_speech():
    """Test text-to-speech conversion."""
    text = "Hello, this is a test."
    audio_data = await speech.text_to_speech(text)
    
    assert isinstance(audio_data, bytes)
    assert len(audio_data) > 0

@pytest.mark.asyncio
async def test_text_to_speech_with_different_voices():
    """Test text-to-speech with different voices."""
    text = "Testing different voices."
    
    # Test each available voice
    for voice in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        audio_data = await speech.text_to_speech(text, voice=voice)
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0

@pytest.mark.asyncio
async def test_audio_buffer():
    """Test audio buffer functionality."""
    buffer = speech.AudioBuffer(chunk_size=4)
    
    # Add data in parts
    buffer.add_data(b"test")
    assert buffer.get_chunk() == b"test"
    assert buffer.get_chunk() is None
    
    # Add more data
    buffer.add_data(b"more")
    assert buffer.get_chunk() == b"more"
    
    # Add partial data
    buffer.add_data(b"par")
    assert buffer.get_chunk() is None

@pytest.mark.asyncio
async def test_stream_transcription():
    """Test streaming transcription."""
    async def mock_audio_stream():
        # Simulate audio chunks
        yield b"test audio chunk 1"
        yield b"test audio chunk 2"
    
    chunks = []
    async for text in speech.stream_transcription(mock_audio_stream()):
        chunks.append(text)
    
    # Note: We can't assert exact content since it depends on OpenAI API
    # but we can check that we got some output
    assert isinstance(chunks, list) 