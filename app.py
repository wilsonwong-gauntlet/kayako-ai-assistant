from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
import sentry_sdk

# Load environment variables
load_dotenv()

# Initialize Sentry if DSN is provided
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        environment=os.getenv("APP_ENV", "development"),
    )

app = FastAPI(
    title="Kayako AI Call Assistant",
    description="Voice-based customer support using AI and Kayako Knowledge Base",
    version="0.1.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

# Twilio webhook endpoint for incoming calls
@app.post("/voice")
async def handle_call(request: Request):
    # TODO: Implement call handling
    return {"message": "Call handling not implemented yet"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("APP_ENV") == "development" else False,
    ) 