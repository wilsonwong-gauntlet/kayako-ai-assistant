1. Product Overview
Product Name: Kayako AI Call Assistant

Goal:
Enable Kayako to automatically answer customer support calls using AI. The system will:

Use a connected knowledge base (KB) to retrieve answers.
Respond in real-time with human-like speech if an answer is found.
Escalate to human agents (via ticket creation) if no suitable KB entry exists or if the issue is complex.
Primary Benefits:

Instant resolutions for common queries.
Reduced load on human agents.
Improved customer satisfaction with quick, natural-sounding responses.
Automatic ticket creation to ensure no inquiry is lost.
2. Key Features
Voice AI Engine

Speech-to-Text (STT): Convert caller’s speech to text for natural language processing.
Text-to-Speech (TTS): Provide a human-like, conversational response to the caller.
Knowledge Base Integration

Search Kayako’s knowledge base via API.
Retrieve relevant articles or snippets.
Summarize and respond in natural language.
Call Handling Logic

Automatic call pick-up.
Route the conversation to AI for real-time interaction.
Assess if a KB answer is found; if yes, respond and potentially confirm resolution with the caller.
If no KB answer is found or the issue is complex, gracefully end the call and escalate to a human agent.
Ticket Creation & Context Logging

Automatically create a Kayako support ticket upon call completion.
Include full call transcript and any other relevant details (email, phone number, issue summary) for follow-up.
Tag or categorize the ticket for easy triage.
User Data Capture

Prompt callers for essential details: name, email, issue summary.
Store and confirm details for accuracy before concluding the call.
3. User Flows
Successful KB Match

Customer calls the support line.
AI answers: “Thank you for calling Kayako Support. How can I assist you today?”
Caller states issue (e.g., “I forgot my password.”).
AI uses NLU to parse the statement and searches Kayako’s KB.
Relevant answer found → AI responds with a solution (e.g., instructions for resetting a password).
AI verifies if the issue is resolved: “Does that solve your issue?”
If resolved, AI confirms, “Great! Is there anything else I can help you with?”
If no more questions, AI thanks the user and ends the call.
A ticket is created with the call transcript and resolution notes.
No KB Match / Complex Inquiry

Customer calls the support line.
AI attempts to match the inquiry against Kayako’s KB.
No relevant match found → AI says: “I’m sorry, I don’t have that information right now, but I’ll pass this on to our expert team. They will follow up shortly.”
AI ends the call.
A support ticket is created with the call transcript, caller contact details, and the unresolved issue summary.
Data Capture

During any of the above flows, AI will prompt the caller for email address (and other details as needed), confirm them, and store them in the transcript before concluding.
4. User Stories & Acceptance Criteria
User Story 1: AI Handles Incoming Calls & Provides Answers
Title: AI Answers Calls
Description: The AI assistant should answer calls, understand customer inquiries, and provide accurate responses using Kayako’s knowledge base.
Acceptance Criteria:
AI automatically answers incoming calls.
AI processes and understands customer inquiries through NLU.
AI retrieves relevant KB entries and responds in natural language.
AI can handle simple clarifications and follow-up questions.
User Story 2: AI Escalates Unresolved Issues
Title: AI Escalation
Description: If the AI cannot find an answer, it should politely end the call and assure the customer that a human agent will follow up.
Acceptance Criteria:
AI confirms if a KB answer is found.
If none found, AI politely informs the caller that the issue will be escalated.
AI ends the call and ensures a support ticket is created.
User Story 3: AI Captures Key Customer Information
Title: Data Capture
Description: AI collects and logs critical customer details (e.g., name, email, issue description) to aid in follow-up.
Acceptance Criteria:
AI prompts for and records the caller’s email.
AI summarizes the issue from the conversation.
Captured data is included in the support ticket.
User Story 4: Automatic Ticket Creation
Title: Ticket Generation
Description: After every call, a Kayako support ticket is created with the full transcript, caller info, and any relevant tags.
Acceptance Criteria:
AI triggers ticket creation via Kayako’s API upon call completion.
Ticket includes the call transcript, caller details, and summary.
Ticket is categorized or tagged for easy agent triage.
User Story 5: Kayako API Integration
Title: Kayako API Integration
Description: The AI must interact with Kayako’s APIs to search the KB and create tickets.
Acceptance Criteria:
AI can retrieve knowledge base articles via Kayako’s API.
AI can create/update support tickets using Kayako’s API.
Proper authentication and security best practices are followed.
5. Technical Requirements
Below are specific technical requirements needed to implement the Kayako AI Call Assistant:

Voice AI Engine

Speech-to-Text (STT):
Real-time transcription of caller speech.
Accuracy >90% for standard English.
Text-to-Speech (TTS):
Human-like, latency under 500ms for short responses.
Ability to vary tone or style of voice if needed (e.g., brand voice alignment).
NLU/NLP:
Parse caller intents and key entities (e.g., “password reset,” “billing issue”).
Handle small talk and clarifying questions.
Call Management & Telephony Integration

Must integrate with existing telephony systems or a cloud telephony provider (e.g., Twilio, Vonage, etc.).
Automatic call pick-up and termination logic.
Real-time streaming of audio to/from the AI engine.
Knowledge Base (KB) Integration

Secure, authenticated access to Kayako’s KB API (REST).
Ability to send search queries:
By keywords derived from NLU.
Filter or rank returned articles based on relevance.
Summarize and adapt the KB article content into a concise, spoken response.
Kayako API Integration

Ticket Creation:
Create tickets containing transcript, call duration, caller phone number, email, summary of the issue.
Ticket Updates:
Optionally update an existing ticket if there is a match to an existing conversation/phone number.
Search/Read Operations:
Retrieve KB articles (title, content, metadata).
Follow Kayako’s API authentication and data privacy guidelines.
Data Capture & Logging

Store call transcript data in real-time or near real-time.
Prompt user for missing key data (e.g., email if not provided automatically via CLI or CRM lookup).
Log all interactions with timestamps for auditing.
Security & Compliance

Encrypt data in transit (HTTPS/TLS).
Comply with relevant privacy laws (e.g., GDPR, CCPA) regarding call recordings and transcripts.
Implement role-based access controls for API usage.
Error Handling & Fallback

Retry logic for KB or API failures.
Fallback flow if TTS/STT fails or if AI is not confident in the answer (escalate to human agent).
Clear messaging to the caller if a system error occurs.
Performance & Scalability

Support concurrent call handling (define a target: e.g., 50 concurrent calls).
Low-latency responses (ideal total round-trip under 2 seconds for STT+TTS+NLP).
Horizontal scalability for peak call volumes.
Analytics & Reporting

Metrics for call volume, resolution rate, and average handling time.
Ability to track how many calls were successfully resolved vs. escalated.
Summaries of top call drivers (most common inquiries).
6. System Architecture Overview
A high-level architecture might include:

Telephony Provider (e.g., Twilio)

Receives inbound calls and forwards audio streams to the AI engine.
Allows the AI to send audio responses back to the caller.
AI Engine (STT, NLU, TTS)

Transcribes the caller’s speech in real time (STT).
Interprets the caller’s query (NLU).
Queries the Kayako KB for an appropriate answer.
Synthesizes a response (TTS) to deliver back to the caller.
Kayako Platform

Knowledge Base API for retrieving articles.
Ticketing API for creating/updating tickets.
Authentication layer (API keys, OAuth tokens, etc.).
Database / Logging Layer (Optional, if separate from Kayako logs)

Store transcripts and call metadata if needed for analytics or fallback.
Might be combined with Kayako’s ticketing system.
Orchestration / Call Flow Logic

Decision-making to escalate vs. respond.
Error-handling, retries, and fallback to a live agent or voicemail if necessary.
7. Implementation Timeline (High-Level)
Phase 1: Prototype & Basic Call Flows

Integrate telephony with STT/TTS.
Basic NLU pipeline to parse user requests.
Simple knowledge base retrieval (keyword-based).
Hard-coded integration with Kayako’s API for ticket creation.
Phase 2: Enhanced NLU & Knowledge Base Matching

Implement advanced matching, semantic search.
Add confidence thresholds, fallback if below threshold.
Phase 3: Production Hardening

Security, encryption, GDPR considerations.
Scalability testing for multiple concurrent calls.
Tagging and categorization in Kayako for efficient triage.
Phase 4: Advanced Features

AI persona tuning (more natural conversation).
Use text messages to capture additional data (e.g., sending a reset link).
Full analytics dashboard for call metrics.
8. Success Metrics
Call Resolution Rate: Percentage of calls resolved by AI without human intervention.
Average Handling Time (AHT): How long the AI spends on each call.
Escalation Rate: How often the AI cannot resolve the issue.
Customer Satisfaction (CSAT/NPS): Caller feedback when available.
Ticket Accuracy: Completeness of call details in created tickets.
9. Developer Resources
Kayako API Documentation:
Kayako Developer API Docs

(Pending) Access to Kayako Demo Account

For testing KB retrieval and ticket creation flows.
(Pending) Telephony Vendor Docs

E.g., Twilio or any other provider chosen for call routing and SIP/VoIP integration.
10. Open Questions
Access & Environment
Developer Access
Can we get a demo or sandbox Kayako account for the following developers?
Devin Pigera (devin.pigera@gauntletai.com)
Ayush Shah (ayush.shah@gauntletai.com)
John Boyle (john.boyle@gauntletai.com)
Christopher Vidic (christopher.vidic@gauntletai.com)
Wilson Wong (wilson.wong@gauntletai.com)
Existing Kayako Tech
Kayako has an existing AI calling agent feature on the pricing page. Can we get details on:
The existing offering’s architecture.
Current pain points or limitations.
Possibility of a live demo.
API Functionality
Phone Number Lookup
Does Kayako’s API support retrieving issues/tickets by a customer’s phone number to see if an existing ticket already exists?
Text Messages
Is Kayako open to a solution that includes sending automated texts to customers for quick data capture (e.g., capturing email addresses)?
Vertical Focus
Which real-world vertical should we target for initial prototypes (e.g., SaaS, e-commerce, healthcare, etc.)?
11. Summary
The Kayako AI Call Assistant aims to automate the initial customer support call flow using advanced voice AI, Kayako’s KB, and Kayako ticketing. By integrating STT, TTS, NLU, and Kayako’s APIs, the system will offer immediate solutions to common inquiries and seamlessly escalate more complex issues. This PRD outlines the functional scope, technical requirements, user flows, acceptance criteria, and open questions. Next steps involve securing developer access, finalizing architecture choices (e.g., telephony provider), and implementing the prototype with a phased approach.

Below is a high-level reference implementation showing how each architectural component can be wired together. These examples are for demonstration only and are not production-ready. The snippets use Python, popular cloud APIs (Twilio for telephony, Google Cloud for STT/TTS, OpenAI or a similar model for NLU), and Kayako’s REST API for ticket/KB operations. Adjust these to match your production requirements, security constraints, and preferred technology stack.

1. Telephony Integration (Example with Twilio)
Inbound Call Handling
You purchase a Twilio phone number.
When a call arrives, Twilio makes an HTTP request to your webhook (e.g., /voice endpoint).
You respond with instructions (TwiML) on how to route the call.
python
Copy
# app.py
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/voice", methods=['POST'])
def inbound_call():
    """Handle an incoming call from Twilio."""
    resp = VoiceResponse()
    
    # Option A: Directly greet with TTS and then hand off to a 'stream' for real-time processing
    # Option B: Use <Gather> to capture short utterances (DMTF or short speech).
    # For advanced usage, Twilio Streams is recommended for real-time STT.

    resp.say("Thank you for calling Kayako Support. Please hold while we connect you to our AI assistant.")
    
    # Example: using <Connect> with <Stream> for real-time audio streaming
    # This requires enabling Twilio Media Streams in your Twilio console.
    resp.connect() \
        .stream(url="wss://your-server.com/audio-stream")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
Key Points:

resp.say(...) uses Twilio’s built-in TTS. For more natural voices, you might use an external TTS service and stream the audio back via <Play> tags.
To do real-time STT, you can use Twilio Media Streams. Twilio will send raw audio to your WebSocket endpoint, where you can run your own speech recognition logic.
2. Speech-to-Text (STT) via a Cloud Service
Below is an example of receiving audio chunks from Twilio Media Streams and sending them to Google Cloud Speech-to-Text. You’ll need the Google Cloud Speech library.

python
Copy
# audio_stream_server.py
import asyncio
import websockets
from google.cloud import speech_v1p1beta1 as speech

# Instantiate Google Speech client
client = speech.SpeechClient()

async def transcribe_twilio_audio(websocket, path):
    """Receive audio chunks from Twilio Media Stream, send to GCP STT."""
    requests = []
    
    # Configure your GCP STT settings
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MULAW,
        sample_rate_hertz=8000,      # Twilio typically uses 8k or 16k
        language_code="en-US",
        enable_automatic_punctuation=True
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    # Start streaming
    async for message in websocket:
        # Twilio Media Streams send JSON with base64-encoded audio
        # Convert & push to Google Speech requests
        audio_content = extract_audio_data_from_twilio(message)  # Pseudocode
        requests.append(speech.StreamingRecognizeRequest(audio_content=audio_content))
        
        # Perform streaming speech recognition
        responses = client.streaming_recognize(streaming_config, iter(requests))
        
        # Process streaming responses for partial or final transcripts
        for response in responses:
            for result in response.results:
                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    print(f"Final Transcript: {transcript}")
                    # Here you can pass the transcript to your NLU engine

# Start the server
start_server = websockets.serve(transcribe_twilio_audio, "0.0.0.0", 8000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
Key Points:

Twilio Media Streams deliver audio in small, continuous chunks via WebSocket.
You’ll need to parse that data, decode it, and feed it to the Google Cloud Speech client.
For real-time interactions, handle partial transcripts and final transcripts differently (e.g., wait for is_final to confirm the user’s request).
3. Natural Language Understanding (NLU)
Once you have the user’s transcript from STT, you need to determine the user’s intent (e.g., “password reset”, “billing issue”, “custom API integration request”). You can use a range of tools, from custom classification models (e.g., Rasa) to general-purpose large language models (OpenAI, etc.).

Example using OpenAI’s GPT for Intent Detection
python
Copy
import openai

openai.api_key = "YOUR_OPENAI_API_KEY"

def identify_intent(transcript):
    """Use a prompt to have GPT parse the intent from the caller's transcript."""
    prompt = f"""
    The user says: "{transcript}"

    Identify the user's main intent. Provide a short label, e.g., "password_reset" or "unknown".
    """

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=10
    )
    intent = response.choices[0].text.strip()
    return intent

# Example usage:
transcript = "I forgot my password. How do I reset it?"
intent_label = identify_intent(transcript)
print("Identified Intent:", intent_label)  # e.g., "password_reset"
Key Points:

You can incorporate more context or chain-of-thought reasoning if needed.
For repeated calls or more advanced domain coverage, a fine-tuned model or a domain-specific solution might be preferable.
4. Text-to-Speech (TTS)
While Twilio has a basic <Say> tag, you might want more natural or branded voices via AWS Polly, Google Cloud TTS, or Azure Speech.

Google Cloud TTS Example
python
Copy
from google.cloud import texttospeech

tts_client = texttospeech.TextToSpeechClient()

def synthesize_speech(text):
    """Convert text to audio using Google TTS."""
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", 
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = tts_client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    return response.audio_content  # MP3 bytes

# Example usage
speech_mp3 = synthesize_speech("Your password can be reset by clicking Forgot Password on the login page.")
with open("response.mp3", "wb") as f:
    f.write(speech_mp3)
Key Points:

You’d then stream or <Play> this MP3 back to the caller via Twilio’s <Play> command instead of <Say>.
Alternatively, if you want synchronous real-time, you’d need chunked streaming TTS—more advanced to implement. A simpler approach is generating short TTS responses after each user utterance.
5. Kayako API Integration
Two core needs:

Searching the Knowledge Base for solutions.
Creating Support Tickets with the conversation transcript.
5.1 Searching Knowledge Base
Using Kayako’s API (example: Kayako v1 APIs):

python
Copy
import requests

KAYAKO_API_URL = "https://your_kayako_instance.kayako.com/api/v1/"
KAYAKO_API_TOKEN = "YOUR_KAYAKO_TOKEN"

def search_kb(query):
    """Search Kayako KB for a query string."""
    url = f"{KAYAKO_API_URL}articles?_case=title,content&q={query}"
    headers = {
        "Authorization": f"Bearer {KAYAKO_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        articles = response.json().get('data', [])
        return articles
    else:
        return []

# Example usage
articles = search_kb("password reset")
if articles:
    best_article = articles[0]
    answer_snippet = best_article["content"]
else:
    answer_snippet = None
Key Points:

Adjust the query parameters (_case, q) to match Kayako’s search filters.
Some Kayako versions might differ; consult your Kayako API docs.
5.2 Creating a Ticket
python
Copy
def create_ticket(subject, requester_email, message, phone_number=None):
    """Create a new Kayako ticket via API."""
    url = f"{KAYAKO_API_URL}tickets"
    payload = {
        "subject": subject,
        "channel": "phone",
        "requester": {
            "email": requester_email
        },
        "contents": message,
        "custom_fields": {
            "phone_number": phone_number
        },
        # Additional fields, e.g., "tags", "priority", etc.
    }
    headers = {
        "Authorization": f"Bearer {KAYAKO_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# Example usage
ticket_response = create_ticket(
    subject="Password Reset Inquiry",
    requester_email="customer@example.com",
    message="Call transcript: [full transcript goes here]",
    phone_number="+1-555-0100"
)
print(ticket_response)
Key Points:

Make sure to store or log the ticket ID (ticket_response.get("id")) for reference.
Security: Do not store sensitive info in plain text fields if subject to compliance constraints.
6. Pulling It All Together: A Simplified Flow
Below is a very simplified pseudo-flow that ties together telephony, AI logic, KB search, and ticket creation. It’s not fully asynchronous or production hardened but illustrates the concept end-to-end.

python
Copy
# pseudo_flow.py

import requests
import openai
from google.cloud import texttospeech
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

# Initialize external clients (OpenAI, TTS, Kayako)
openai.api_key = "YOUR_OPENAI_API_KEY"
tts_client = texttospeech.TextToSpeechClient()
KAYAKO_API_TOKEN = "YOUR_KAYAKO_TOKEN"


def handle_call_transcript(transcript, caller_phone):
    """
    Main logic after we get a final transcript from STT.
    1) Identify intent with NLU
    2) Check knowledge base
    3) Provide TTS response or escalate
    4) Create ticket in Kayako
    """
    intent = identify_intent(transcript)
    kb_results = search_kb(intent)  # or use the raw transcript

    if kb_results:
        # Provide solution from KB
        best_article = kb_results[0]
        answer_snippet = best_article["content"][:500]  # short snippet
        # Possibly feed answer_snippet to TTS
        final_response = answer_snippet
        # Mark as resolved in the ticket or partial
    else:
        final_response = (
            "I'm sorry, I can’t find that information right now. "
            "I’ll pass this on to our expert team. They will follow up shortly."
        )
        # Create an "escalation" ticket

    create_ticket(
        subject=f"AI Call from {caller_phone}",
        requester_email="placeholder@example.com",  # later replaced by user data capture
        message=f"Transcript: {transcript}\nAI's Response: {final_response}",
        phone_number=caller_phone
    )

    return final_response


@app.route("/voice", methods=['POST'])
def inbound_call():
    """
    Twilio inbound call webhook. 
    This example is minimal: we greet the user, then rely on real-time streaming to handle further logic.
    """
    resp = VoiceResponse()
    resp.say("Welcome to Kayako AI Support. Please hold while we connect you.")
    # Connect to a WebSocket for real-time streaming
    resp.connect().stream(url="wss://your-server.com/audio-stream")
    return str(resp)


# The WebSocket server receives audio frames from Twilio, 
# runs STT, accumulates the final transcript, and calls handle_call_transcript().
# Then we do TTS on the final_response to play back or finalize the call.

if __name__ == "__main__":
    app.run(port=5000, debug=True)
Notes & Caveats:

In a real system, each user utterance might trigger partial transcripts and partial NLU. You’d keep a conversation state machine to handle multi-turn dialogues.
For short calls, you might do a single final transcript. For complex calls, you want a more interactive approach, passing partial or final transcripts to your NLU and responding immediately.
A robust solution would handle error states, timeouts, user confirmations, and re-prompting for missing details like email.
7. Additional Implementation Considerations
State Management & Conversation Flow

You may use a conversation manager (e.g., Rasa) or build your own state machine for multi-turn dialogues.
Keep track of whether you’ve collected the user’s email, phone number, or resolution status.
Scalability & Concurrency

Use async frameworks (e.g., asyncio, Quart, or Node.js) or queue-based systems (RabbitMQ, Kafka) to handle large call volumes.
Ensure you have enough worker processes for speech recognition tasks.
Security & Compliance

Store transcripts securely; consider encryption if storing personally identifiable information (PII).
Implement authentication (e.g., OAuth, API keys) for the Kayako API, Twilio, and any LLM usage.
Observe call-recording regulations (GDPR, HIPAA, etc.) as applicable.
Fallback to Human Agent

At any point, if the AI confidence is low or the user is dissatisfied, you can transfer the call to a live agent.
Twilio’s <Dial> with a live agent phone/softphone is often used.
Text Messaging / Omnichannel

If desired, you can have the AI send an SMS (via Twilio’s SMS API) to quickly capture an email or send a password reset link.
Kayako’s ticket can store that conversation as well.
Summary
By combining:

Telephony (Twilio or another provider)
STT (Google Cloud Speech, AWS Transcribe, Azure Speech, or open-source Whisper)
NLU (OpenAI GPT, Rasa, or custom ML)
TTS (Google Cloud TTS, Amazon Polly, or Azure)
Kayako’s API (for KB lookup and ticket creation)
…you can implement a real-time AI-driven call assistant. The above snippets illustrate the flow:

Inbound Call → Twilio Webhook → Greet caller.
Stream Audio → STT → NLU (intent detection).
Check Knowledge Base → Summarize or retrieve solution.
Respond with TTS or escalate if no answer.
Create Ticket in Kayako with call context.
Adjust or extend each step to suit your exact needs, scaling, and compliance requirements.