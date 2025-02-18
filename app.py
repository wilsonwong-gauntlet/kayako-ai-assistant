"""Main application entry point."""

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
import sentry_sdk
from twilio.request_validator import RequestValidator
import logging

from src.voice.twilio_handler import TwilioHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is provided and not a placeholder
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn and not sentry_dsn.startswith("your_"):
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        environment=os.getenv("APP_ENV", "development"),
    )

app = FastAPI(
    title="Kayako AI Call Assistant",
    description="Voice-based customer support using AI and Kayako Knowledge Base",
    version="0.1.0",
)

# Initialize Twilio handler
twilio_handler = TwilioHandler()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def validate_twilio_request(request: Request) -> bool:
    """Validate that the request is from Twilio."""
    validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))
    
    # Get the URL and POST data
    url = str(request.url)
    post_data = await request.form()
    
    # Get the X-Twilio-Signature header
    signature = request.headers.get("X-Twilio-Signature", "")
    
    return validator.validate(url, dict(post_data), signature)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Validate Twilio setup
    twilio_ok = await twilio_handler.validate_twilio_number()
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "twilio_configured": twilio_ok
    }

# Twilio webhook endpoint for incoming calls
@app.post("/voice")
async def handle_call(request: Request):
    """Handle incoming Twilio voice calls."""
    # Skip signature validation in development mode
    if os.getenv("APP_ENV") != "development":
        if not await validate_twilio_request(request):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    
    try:
        # Get call data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        
        if not call_sid:
            raise HTTPException(status_code=400, detail="CallSid not provided")
        
        logger.info(f"New call received - SID: {call_sid}")
        
        # Handle the call
        twiml_response = await twilio_handler.handle_incoming_call(call_sid)
        
        # Set content type for TwiML
        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error in handle_call: {str(e)}")
        raise

# Handle transcribed speech
@app.post("/voice/transcription")
async def handle_transcription(request: Request):
    """Handle transcribed speech from Twilio."""
    # Skip signature validation in development mode
    if os.getenv("APP_ENV") != "development":
        if not await validate_twilio_request(request):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    
    try:
        # Get transcription data
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        transcript = form_data.get("SpeechResult")
        confidence = float(form_data.get("Confidence", 0))
        
        if not all([call_sid, transcript]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        logger.info(f"Call {call_sid} - User said: {transcript} (confidence: {confidence})")
        
        # Handle the transcription
        twiml_response = await twilio_handler.handle_transcription(
            call_sid,
            transcript,
            confidence
        )
        
        # Log the assistant's response (extract text from TwiML)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(twiml_response)
        for say in root.findall(".//Say"):
            logger.info(f"Call {call_sid} - Assistant response: {say.text}")
        
        # Set content type for TwiML
        return Response(content=twiml_response, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error in handle_transcription: {str(e)}")
        raise

# Handle call status updates
@app.post("/voice/status")
async def handle_call_status(request: Request):
    """Handle call status updates from Twilio."""
    # Validate request is from Twilio
    if not await validate_twilio_request(request):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    
    # Get status data
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    status = form_data.get("CallStatus")
    
    logger.info(f"Call {call_sid} - Status changed to: {status}")
    
    if status == "completed":
        twilio_handler.end_call(call_sid)
        logger.info(f"Call {call_sid} - Conversation ended")
    
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("APP_ENV") == "development" else False,
    ) 