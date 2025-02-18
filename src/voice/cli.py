"""CLI tools for testing voice functionality."""

import asyncio
import click
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
from pathlib import Path
from . import speech

@click.group()
def cli():
    """Voice processing test tools."""
    pass

@cli.command()
@click.argument('text')
@click.option('--voice', default='alloy', help='Voice to use (alloy, echo, fable, onyx, nova, shimmer)')
def speak(text: str, voice: str):
    """Convert text to speech and play it."""
    async def _speak():
        audio_data = await speech.text_to_speech(text, voice=voice)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Play the audio
        data, samplerate = sf.read(temp_path)
        sd.play(data, samplerate)
        sd.wait()  # Wait until audio is done playing
        
        # Clean up
        Path(temp_path).unlink()
    
    asyncio.run(_speak())

@cli.command()
@click.option('--duration', default=5, help='Recording duration in seconds')
def record(duration: int):
    """Record audio and transcribe it."""
    async def _record_and_transcribe():
        # Record audio
        print(f"Recording for {duration} seconds...")
        recording = sd.rec(
            int(duration * 44100),
            samplerate=44100,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
        print("Recording finished.")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, recording, 44100)
            
            # Transcribe
            print("Transcribing...")
            transcription = await speech.transcribe_audio(temp_file.name)
            print(f"Transcription: {transcription}")
            
            # Clean up
            Path(temp_file.name).unlink()
    
    asyncio.run(_record_and_transcribe())

if __name__ == '__main__':
    cli() 