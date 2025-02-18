# Kayako AI Call Assistant

An intelligent call assistant that integrates with Kayako's knowledge base to provide automated customer support through voice interactions.

## Features

- Voice-based customer support using OpenAI's Whisper and TTS
- Integration with Kayako Knowledge Base
- Automatic ticket creation and escalation
- Real-time conversation handling with GPT
- Secure PII handling

## Prerequisites

- Python 3.9+
- OpenAI API key
- Twilio account and phone number
- Kayako instance with API access

## Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/kayako-ai-assistant.git
cd kayako-ai-assistant
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Run the development server:
```bash
python app.py
```

## Project Structure

```
├── app.py                 # Main application entry point
├── config/               # Configuration files
├── src/
│   ├── voice/           # Voice processing modules
│   ├── kb/              # Knowledge base integration
│   ├── conversation/    # Conversation handling
│   └── tickets/         # Ticket management
├── tests/               # Test files
└── docs/                # Documentation
```

## Development

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Write tests for new features
- Update documentation as needed

## Security

- Never commit API keys or sensitive credentials
- Follow security best practices for handling PII
- Use environment variables for sensitive configuration

## License

[MIT License](LICENSE) 