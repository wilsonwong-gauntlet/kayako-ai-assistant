"""Twilio integration for voice calls."""

import os
from typing import Optional
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import sentry_sdk
from time import time

from ..conversation.flow import ConversationFlowManager
from .speech import text_to_speech
from . import config
from ..monitoring.metrics import metrics_manager

# Load environment variables
load_dotenv()

class TwilioHandler:
    """Handles Twilio voice call interactions."""
    
    def __init__(self):
        """Initialize Twilio client and conversation manager."""
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.conversation_manager = ConversationFlowManager()
        self.call_conversations = {}  # Map call SIDs to conversation IDs
    
    def _configure_voice_response(self, response: VoiceResponse, text: str) -> None:
        """Configure voice response with enhanced settings."""
        response.say(
            text,
            voice=config.VOICE_NAME,
            language=config.VOICE_LANGUAGE,
            rate=config.VOICE_RATE
        )
    
    def _configure_gather(self, response: VoiceResponse) -> Gather:
        """Configure speech recognition with enhanced settings."""
        gather = Gather(
            input='speech',
            action='/voice/transcription',
            method='POST',
            language=config.TWILIO_INPUT_LANGUAGE,
            speechTimeout=config.TWILIO_SPEECH_TIMEOUT,
            speechModel=config.TWILIO_SPEECH_MODEL,
            enhanced=True,
            profanityFilter=config.TWILIO_PROFANITY_FILTER,
            interimSpeechResultsCallback='/voice/interim' if config.TWILIO_INTERIM_SPEECH_RESULTS else None,
            speechEndThreshold=config.TWILIO_SPEECH_END_THRESHOLD
        )
        return gather
    
    async def handle_incoming_call(self, call_sid: str) -> str:
        """
        Handle an incoming call and return TwiML response.
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            TwiML response as string
        """
        # Start metrics tracking for new call
        metrics_manager.start_call(call_sid)
        
        # Start new conversation
        conversation_id, greeting = await self.conversation_manager.start_conversation()
        self.call_conversations[call_sid] = conversation_id
        
        # Create TwiML response
        response = VoiceResponse()
        
        # Add initial greeting with enhanced voice settings
        self._configure_voice_response(response, greeting)
        
        # Start gathering user input with enhanced settings
        gather = self._configure_gather(response)
        self._configure_voice_response(gather, "Please speak after the tone.")
        response.append(gather)
        
        # Add fallback with enhanced voice settings
        self._configure_voice_response(
            response,
            "I didn't hear anything. Please call back and try again."
        )
        response.hangup()
        
        return str(response)
    
    async def handle_transcription(
        self,
        call_sid: str,
        transcript: str,
        confidence: float
    ) -> str:
        """
        Handle transcribed speech and return TwiML response.
        
        Args:
            call_sid: Twilio Call SID
            transcript: Transcribed text
            confidence: Transcription confidence score
            
        Returns:
            TwiML response as string
        """
        # Get call metrics
        metrics = metrics_manager.get_call_metrics(call_sid)
        if metrics:
            metrics.track_transcription(confidence)
        
        try:
            start_time = time()
            
            # Get associated conversation
            conversation_id = self.call_conversations.get(call_sid)
            if not conversation_id:
                # Start new conversation if none exists
                conversation_id, _ = await self.conversation_manager.start_conversation()
                self.call_conversations[call_sid] = conversation_id
            
            # Process message through conversation flow
            response_text = await self.conversation_manager.process_message(
                conversation_id,
                transcript
            )
            
            # Create TwiML response
            response = VoiceResponse()
            
            # Add assistant's response with enhanced voice settings
            self._configure_voice_response(response, response_text)
            
            # Continue gathering user input with enhanced settings
            gather = self._configure_gather(response)
            response.append(gather)
            
            # Track processing time if metrics exist
            if metrics:
                processing_time = time() - start_time
                sentry_sdk.set_measurement("response_time", processing_time, unit="second")
            
            return str(response)
                
        except Exception as e:
            # Capture exception with context
            sentry_sdk.capture_exception(
                e,
                extras={
                    "call_sid": call_sid,
                    "transcript": transcript,
                    "confidence": confidence
                }
            )
            # Create error response
            error_response = VoiceResponse()
            self._configure_voice_response(
                error_response,
                "I'm sorry, but I encountered an error processing your request. Please try again."
            )
            return str(error_response)
    
    def end_call(self, call_sid: str) -> None:
        """Clean up resources when call ends."""
        # End metrics tracking
        metrics_manager.end_call(call_sid)
        # Clean up conversation mapping
        self.call_conversations.pop(call_sid, None)
    
    async def validate_twilio_number(self) -> bool:
        """Validate that the configured Twilio phone number exists and is properly set up."""
        try:
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=os.getenv("TWILIO_PHONE_NUMBER")
            )
            return len(numbers) > 0
        except TwilioRestException:
            return False
    
    async def configure_webhook(self, webhook_url: str) -> bool:
        """
        Configure webhook URL for the Twilio phone number.
        
        Args:
            webhook_url: Full URL for the voice webhook
            
        Returns:
            True if successful, False otherwise
        """
        try:
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=os.getenv("TWILIO_PHONE_NUMBER")
            )
            
            if not numbers:
                return False
            
            # Update webhook URL
            number = numbers[0]
            number.update(
                voice_url=webhook_url,
                voice_method='POST'
            )
            
            return True
        except TwilioRestException:
            return False 