from fastapi import APIRouter, Request
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter()

@router.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice calls."""
    response = VoiceResponse()
    # TODO: Add initial greeting
    # TODO: Start recording/streaming
    return response.to_xml()

@router.post("/voice/stream")
async def handle_audio_stream(request: Request):
    """Handle real-time audio stream from Twilio."""
    # TODO: Process audio chunks
    # TODO: Send to Whisper API
    pass 