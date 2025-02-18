"""Script to configure Twilio settings."""

import asyncio
import click
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import os

from .twilio_handler import TwilioHandler

@click.group()
def cli():
    """Twilio configuration tools."""
    pass

@cli.command()
def validate_setup():
    """Validate Twilio configuration."""
    async def _validate():
        handler = TwilioHandler()
        is_valid = await handler.validate_twilio_number()
        
        if is_valid:
            print("✅ Twilio phone number is properly configured")
        else:
            print("❌ Twilio phone number validation failed")
            print("\nPlease check:")
            print("1. TWILIO_ACCOUNT_SID is correct")
            print("2. TWILIO_AUTH_TOKEN is correct")
            print("3. TWILIO_PHONE_NUMBER exists and is owned by your account")
    
    asyncio.run(_validate())

@cli.command()
@click.option('--area-code', help='Desired area code for the phone number')
@click.option('--country', default='US', help='Country code (default: US)')
def purchase_number(area_code: str, country: str):
    """Purchase a new Twilio phone number."""
    load_dotenv()
    
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )
    
    try:
        # Search for available numbers
        numbers = client.available_phone_numbers(country).local.list(
            area_code=area_code,
            voice_enabled=True,
            sms_enabled=False
        )
        
        if not numbers:
            print(f"❌ No available numbers found in area code {area_code}")
            return
        
        # Purchase the first available number
        number = client.incoming_phone_numbers.create(
            phone_number=numbers[0].phone_number,
            voice_url=f"{os.getenv('BASE_URL', 'http://localhost:8000')}/voice",
            status_callback=f"{os.getenv('BASE_URL', 'http://localhost:8000')}/voice/status"
        )
        
        print(f"✅ Successfully purchased number: {number.phone_number}")
        print("\nAdd this number to your .env file as TWILIO_PHONE_NUMBER")
        
    except TwilioRestException as e:
        print(f"❌ Error purchasing number: {str(e)}")

@cli.command()
@click.option('--url', help='Base URL for webhooks (e.g., https://your-domain.com)')
def configure_webhooks(url: str):
    """Configure webhooks for an existing Twilio number."""
    async def _configure():
        handler = TwilioHandler()
        success = await handler.configure_webhook(f"{url}/voice")
        
        if success:
            print("✅ Webhook URLs configured successfully")
            print(f"\nWebhook endpoints:")
            print(f"Voice: {url}/voice")
            print(f"Transcription: {url}/voice/transcription")
            print(f"Status: {url}/voice/status")
        else:
            print("❌ Failed to configure webhook URLs")
            print("\nPlease check:")
            print("1. Your Twilio credentials are correct")
            print("2. The phone number exists in your account")
            print("3. The URL is accessible")
    
    asyncio.run(_configure())

if __name__ == '__main__':
    cli() 