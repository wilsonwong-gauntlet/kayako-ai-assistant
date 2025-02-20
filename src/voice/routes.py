from fastapi import APIRouter, Request
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Gather
from typing import Dict, Optional
import logging

from .speech import transcribe_audio, text_to_speech
from ..conversation.flow import ConversationFlowManager
from . import config

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active call handlers with conversation IDs
active_calls: Dict[str, Dict[str, str]] = {}  # call_sid -> {conversation_id, state}

@router.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice calls."""
    try:
        # Get call data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        
        # Log all form data for debugging
        logger.info(f"Initial call form data: {dict(form_data)}")
        
        if not call_sid:
            raise ValueError("CallSid not provided")
            
        logger.info(f"New call received - SID: {call_sid}")
        
        # Initialize conversation manager for this call
        conversation_manager = ConversationFlowManager()
        conversation_id, greeting = await conversation_manager.start_conversation()
        
        # Store the mapping of call_sid to conversation_id
        active_calls[call_sid] = {"conversation_id": conversation_id, "state": "COLLECTING_ISSUE"}
        
        # Check if we already have speech
        speech_result = form_data.get("SpeechResult")
        
        # Create TwiML response
        response = VoiceResponse()
        
        if speech_result:
            # Process the initial speech
            logger.info(f"Processing initial speech: {speech_result}")
            assistant_response = await conversation_manager.process_message(
                conversation_id,  # Use conversation_id instead of call_sid
                speech_result
            )
            # Say the response
            response.say(
                assistant_response,
                voice=config.VOICE_NAME,
                language=config.VOICE_LANGUAGE
            )
        else:
            # No initial speech, give greeting
            response.say(
                greeting or "Welcome to Kayako Support. How can I help you today?",
                voice=config.VOICE_NAME,
                language=config.VOICE_LANGUAGE
            )
        
        # Set up speech recognition for next input
        gather = Gather(
            input='speech',
            action='/voice/transcription',
            method='POST',
            language=config.TWILIO_INPUT_LANGUAGE,
            speechTimeout=config.TWILIO_SPEECH_TIMEOUT,
            speechModel=config.TWILIO_SPEECH_MODEL,
            enhanced=True
        )
        response.append(gather)
        
        # Add fallback in case of no input
        response.say(
            "I didn't hear anything. Please try again.",
            voice=config.VOICE_NAME,
            language=config.VOICE_LANGUAGE
        )
        
        return response.to_xml()
        
    except Exception as e:
        logger.error(f"Error in handle_incoming_call: {str(e)}")
        raise

@router.post("/voice/transcription")
async def handle_transcription(request: Request):
    """Handle transcribed speech from Twilio."""
    try:
        # Get transcription data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        transcript = form_data.get("SpeechResult")
        confidence = float(form_data.get("Confidence", 0))
        
        if not all([call_sid, transcript]):
            raise ValueError("Missing required parameters")
        
        logger.info(f"Call {call_sid} - User said: {transcript} (confidence: {confidence})")
        
        # Get the conversation ID for this call
        call_data = active_calls.get(call_sid)
        if not call_data:
            logger.error(f"No conversation data found for call {call_sid}")
            # Create a new conversation as fallback
            conversation_manager = ConversationFlowManager()
            conversation_id, _ = await conversation_manager.start_conversation()
            active_calls[call_sid] = {"conversation_id": conversation_id, "state": "COLLECTING_ISSUE"}
            call_data = active_calls[call_sid]
        
        # Create a new conversation manager and process the message
        conversation_manager = ConversationFlowManager()
        response = await conversation_manager.process_message(
            call_data["conversation_id"],  # Use the stored conversation_id
            transcript
        )
        
        # Create TwiML response
        twiml = VoiceResponse()
        
        if response:
            logger.info(f"Call {call_sid} - Assistant response: {response}")
            # Add the response
            twiml.say(response, voice=config.VOICE_NAME, language=config.VOICE_LANGUAGE)
        
        # Set up next speech recognition
        gather = Gather(
            input='speech',
            action='/voice/transcription',
            method='POST',
            language=config.TWILIO_INPUT_LANGUAGE,
            speechTimeout=config.TWILIO_SPEECH_TIMEOUT,
            speechModel=config.TWILIO_SPEECH_MODEL,
            enhanced=True
        )
        twiml.append(gather)
        
        return twiml.to_xml()
        
    except Exception as e:
        logger.error(f"Error in handle_transcription: {str(e)}")
        # Create error response
        twiml = VoiceResponse()
        twiml.say(
            "I'm sorry, I encountered an error. Please try again.",
            voice=config.VOICE_NAME,
            language=config.VOICE_LANGUAGE
        )
        return twiml.to_xml()

@router.websocket("/voice/stream")
async def handle_audio_stream(websocket: WebSocket):
    """Handle real-time audio stream from Twilio."""
    call_sid: Optional[str] = None
    
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        async for message in websocket.iter_json():
            if message.get("event") == "start":
                # Extract call SID from start message
                call_sid = message["start"]["callSid"]
                logger.info(f"Started streaming for call {call_sid}")
                
            elif message.get("event") == "media":
                if not call_sid or call_sid not in active_calls:
                    logger.error(f"No conversation manager found for call {call_sid}")
                    continue
                    
                # Get the existing conversation manager
                conversation_manager = active_calls[call_sid]
                
                # Process audio chunk
                chunk = base64.b64decode(message["media"]["payload"])
                
                # TODO: Implement chunked audio processing with Whisper
                # For now, we'll use basic transcription
                transcript = await transcribe_audio(chunk)
                
                if transcript:
                    logger.info(f"Call {call_sid} - User said: {transcript}")
                    # Process through existing conversation flow
                    response = await conversation_manager.process_message(
                        call_sid,  # Use call_sid as conversation_id
                        transcript
                    )
                    
                    if response:
                        logger.info(f"Call {call_sid} - Assistant response: {response}")
                        # Convert response to audio
                        audio_response = await text_to_speech(response)
                        
                        # Send audio back to client
                        await websocket.send_bytes(audio_response)
                
            elif message.get("event") == "stop":
                logger.info(f"Streaming ended for call {call_sid}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in handle_audio_stream: {str(e)}")
    finally:
        if call_sid:
            # Clean up the conversation manager
            active_calls.pop(call_sid, None) 