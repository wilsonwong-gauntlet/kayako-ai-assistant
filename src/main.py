"""Main FastAPI application."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ssl
from kb.config import kayako_settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app
app = FastAPI(
    title="Kayako AI Assistant",
    description="AI-powered voice assistant for Kayako support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    # SSL configuration for HTTPS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ssl_context.load_cert_chain(
            certfile="certs/server.crt",
            keyfile="certs/server.key"
        )
    except FileNotFoundError:
        logging.warning(
            "SSL certificates not found. Running without HTTPS. "
            "Please generate certificates for production use."
        )
        ssl_context = None
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_certfile="certs/server.crt" if ssl_context else None,
        ssl_keyfile="certs/server.key" if ssl_context else None,
        reload=True  # Set to False in production
    ) 