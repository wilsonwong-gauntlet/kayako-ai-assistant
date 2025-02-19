Below is a comprehensive overview of Kayako’s REST API, how it is structured, how authentication works, and how you might use it to integrate with a voice service (or any other application). This guide is intentionally very detailed, to help an AI agent (or any developer) understand the nuances of Kayako’s API and how to interact with it.

1. High-Level Overview
Kayako is a helpdesk and customer support platform. The Kayako REST API allows external systems and applications to perform the core actions you would handle in the Kayako web interface, such as:

Creating new conversations (tickets)
Retrieving and updating existing conversations
Managing customers (end-users)
Managing support agents
Handling messages in conversations (adding replies, notes, etc.)
Working with organizations
Searching through customer data
The API typically follows RESTful conventions, using clear endpoints for each resource. JSON is used as the data exchange format. Each call you make to Kayako’s REST API must be properly authenticated.

2. Authentication
The Kayako REST API supports different methods of authentication. Most commonly, you will use OAuth 2.0 or Personal Access Tokens.

2.1. OAuth 2.0 (if enabled in your Kayako instance)
Obtain OAuth Client Credentials:

You’ll need a client_id and client_secret from your Kayako administration settings.
Obtain an Access Token:

Typically, you’ll send a request (e.g., POST /api/v1/oauth/token) with your client credentials in the body, asking for a token (often using the “client_credentials” grant type or whichever flow is supported).
You’ll receive a JSON response containing an access_token, which you’ll then include in all subsequent requests.
Using the Token:

Pass the token in the Authorization header. For example:
makefile
Copy
Authorization: Bearer <your_access_token>
2.2. Personal Access Tokens / API Key
Some Kayako installations also support personal API tokens. If you receive an api_key and secret_key, you may be able to use them directly in the request headers. The header format often looks like:

css
Copy
Authorization: Basic <base64_encoded("api_key:secret_key")>
or sometimes as:

makefile
Copy
X-Api-Key: <api_key>
X-Api-Secret: <secret_key>
Check your Kayako admin panel or official Kayako documentation for the exact method used by your instance. OAuth 2.0 is generally the most common in Kayako’s newer platform.

3. Endpoints and Common Entities
Kayako’s REST API is typically served from a base URL similar to:

perl
Copy
https://<your_kayako_domain>/api/v1
All resources are nested beneath this path. The key resources in Kayako are:

Conversations (/conversations)
Users (/users)
Organizations (/organizations)
Messages (nested under conversations: /conversations/{conversation_id}/messages)
Search (/search)
Below is a deeper look at how these endpoints are structured and used.

4. Working with Conversations
4.1. Creating a Conversation (Ticket)
Endpoint: POST /conversations

Description: Creates a new conversation (akin to a new ticket).

Request Body: JSON with fields such as:

json
Copy
{
  "subject": "Subject of the conversation",
  "channel": "Email",
  "requester": {
    "id": 12345
  },
  "messages": [
    {
      "type": "note" | "reply",
      "content": "The body of the conversation message"
    }
  ],
  "assignee": {
    "id": 67890
  }
}
subject: Title or main summary
channel: Where the request originated (e.g., “Email”, “Chat”, “Web”, etc.)
requester: The user who initiated the conversation. You can specify by id or by email.
messages: An array of message objects. Each message has a type (could be "reply" for public replies or "note" for internal notes only visible to agents).
assignee: Optional object specifying which agent is responsible for the conversation (if you have that logic in place).
Sample Request:

bash
Copy
curl -X POST "https://<your_kayako_domain>/api/v1/conversations" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Issue with Logging In",
       "channel": "Email",
       "requester": { "email": "customer@example.com" },
       "messages": [
         {
           "type": "reply",
           "content": "I am having trouble logging into my account."
         }
       ]
     }'
Sample Response:

json
Copy
{
  "resource": "conversation",
  "id": 34567,
  "subject": "Issue with Logging In",
  "channel": "Email",
  "requester": { ... },
  "messages": [ ... ],
  "assignee": null,
  "created_at": "2025-01-01T12:00:00Z",
  ...
}
4.2. Retrieving Conversations
Endpoint: GET /conversations

Description: Retrieves a paginated list of all conversations you have permission to see.

Query Parameters:

include=... to embed related data such as requester or assignee.
status=open|closed|archived to filter by status.
page and limit for pagination.
Sample Request:

bash
Copy
curl -X GET "https://<your_kayako_domain>/api/v1/conversations?include=requester,assignee&status=open&page=1&limit=25" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
Sample Response:

json
Copy
{
  "resource": "collection",
  "data": [
    {
      "resource": "conversation",
      "id": 34567,
      "subject": "Issue with Logging In",
      "requester": { ... },
      "assignee": { ... },
      "status": "open",
      ...
    },
    {
      "resource": "conversation",
      "id": 34568,
      "subject": "Question about pricing",
      "requester": { ... },
      ...
    }
  ],
  "count": 2,
  "total_count": 42
}
4.3. Retrieving a Single Conversation
Endpoint: GET /conversations/{id}
Sample Request:
bash
Copy
curl -X GET "https://<your_kayako_domain>/api/v1/conversations/34567?include=messages,requester,assignee" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
Sample Response:
json
Copy
{
  "resource": "conversation",
  "id": 34567,
  "subject": "Issue with Logging In",
  "requester": { ... },
  "assignee": { ... },
  "messages": [
    {
      "id": 1111,
      "content": "I am having trouble logging into my account.",
      "type": "reply",
      "creator": { ... },
      "created_at": "2025-01-01T12:00:00Z"
    },
    ...
  ],
  ...
}
4.4. Updating a Conversation
Endpoint: PUT /conversations/{id}
Description: Update properties such as subject, status, assignee, etc.
Sample Request:
bash
Copy
curl -X PUT "https://<your_kayako_domain>/api/v1/conversations/34567" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Updated Issue with Logging In",
       "assignee": {
         "id": 67890
       },
       "status": "closed"
     }'
Sample Response:
json
Copy
{
  "resource": "conversation",
  "id": 34567,
  "subject": "Updated Issue with Logging In",
  "status": "closed",
  "assignee": { "id": 67890, ... },
  ...
}
4.5. Adding Messages to a Conversation
Endpoint: POST /conversations/{conversation_id}/messages
Description: Add a new reply or note to a conversation.
Request Body:
json
Copy
{
  "content": "Here's an update on your issue...",
  "type": "reply" | "note"
}
Sample Request:
bash
Copy
curl -X POST "https://<your_kayako_domain>/api/v1/conversations/34567/messages" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "content": "We have reset your password. Please try again.",
       "type": "reply"
     }'
Sample Response:
json
Copy
{
  "resource": "message",
  "id": 2222,
  "type": "reply",
  "content": "We have reset your password. Please try again.",
  ...
}
5. Working with Users
Users in Kayako represent both your customers (end-users) and potentially your agents (depending on roles and permissions).

5.1. Creating a User
Endpoint: POST /users
Sample Request:
bash
Copy
curl -X POST "https://<your_kayako_domain>/api/v1/users" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "fullname": "Jane Doe",
       "email": "jane.doe@example.com",
       "organizations": [
         {
           "id": 123
         }
       ]
     }'
Sample Response:
json
Copy
{
  "resource": "user",
  "id": 54321,
  "fullname": "Jane Doe",
  "email": "jane.doe@example.com",
  "organizations": [ ... ],
  ...
}
5.2. Listing Users
Endpoint: GET /users
Query Parameters: page, limit, search (some Kayako instances allow search=querystring).
Sample Request:
bash
Copy
curl -X GET "https://<your_kayako_domain>/api/v1/users?search=jane.doe@example.com" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
Sample Response:
json
Copy
{
  "resource": "collection",
  "data": [
    {
      "resource": "user",
      "id": 54321,
      "fullname": "Jane Doe",
      "email": "jane.doe@example.com",
      ...
    }
  ],
  "count": 1,
  "total_count": 1
}
5.3. Updating a User
Endpoint: PUT /users/{id}
Sample Request:
bash
Copy
curl -X PUT "https://<your_kayako_domain>/api/v1/users/54321" \
     -H "Authorization: Bearer <YOUR_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "fullname": "Jane A. Doe"
     }'
Sample Response:
json
Copy
{
  "resource": "user",
  "id": 54321,
  "fullname": "Jane A. Doe",
  ...
}
6. Organizations
Organizations represent business entities (or groups of end-users). They are useful for grouping users or tying them to a company account. The endpoints are quite similar:

Create: POST /organizations
List: GET /organizations
Get Single: GET /organizations/{id}
Update: PUT /organizations/{id}
7. Searching
Kayako provides search endpoints to find resources (conversations, users, etc.) by keywords or other criteria:

Endpoint: GET /search

Query Parameters:

query=<search_string>
type=conversation|user|organization (some instances allow searching across multiple types)
Pagination (e.g., page and limit)
Sample Request:

bash
Copy
curl -X GET "https://<your_kayako_domain>/api/v1/search?type=conversation&query=reset+password" \
     -H "Authorization: Bearer <YOUR_TOKEN>"
Sample Response:

json
Copy
{
  "resource": "collection",
  "data": [
    {
      "resource": "conversation",
      "id": 34567,
      "subject": "Issue with Logging In",
      ...
    },
    ...
  ]
}
8. Handling Rate Limits
Kayako (particularly the SaaS version) may impose rate limits on API calls. Typically, if you exceed these limits, you will receive an HTTP 429 (Too Many Requests) response. Be sure to handle retry logic if your application or voice service might make many calls in quick succession.

9. Error Handling and Response Codes
2xx – Success
4xx – Client errors (authentication, missing parameters, etc.)
400 for bad requests,
401 for unauthorized / invalid token,
404 for not found, etc.
5xx – Server errors on Kayako’s side.
Check the response body if you get a 4xx or 5xx for detailed error information. Often it’s in a JSON object like:

json
Copy
{
  "errors": [
    {
      "code": "invalid_parameter",
      "message": "The 'requester.email' field is required."
    }
  ]
}
10. Best Practices for Integrating with a Voice Service (AI Agent)
Authentication Management:

Your AI agent should securely store and refresh tokens as needed. If using OAuth, handle token expiration gracefully and obtain a new token before the old one expires.
Entity Mapping:

Voice commands might refer to “open a new ticket,” “find user John Doe,” etc. You will map those commands to the correct Kayako API endpoints:
“Open a new ticket” → POST /conversations
“Find user John Doe” → GET /search?type=user&query=John+Doe or GET /users?search=...
Conversational Flow:

If your voice service is “reading” conversation history, you can use GET /conversations/{id}?include=messages to retrieve the thread of messages. Then parse them (they’re in JSON) and convert them into voice form.
Error Recovery:

If Kayako responds with an error (e.g., 400 or 429), instruct your AI agent or voice interface to gracefully report the error to the user or prompt for correction (e.g., “I wasn’t able to update that ticket. Would you like to try again?”).
Security & Privacy:

Consider that voice systems may read out sensitive information. Ensure you have appropriate permissions in Kayako and that your agent only accesses data it’s allowed to access.
Mask or skip certain fields if they contain personally identifiable information (PII) or sensitive info that should not be publicly read out.
Caching and Minimizing API Calls:

To avoid hitting rate limits and to keep the voice response quick, you can cache recently retrieved data (e.g., conversation statuses) for short periods. This can speed up the conversation flow and reduce overhead.
11. Putting It All Together: A Sample Use Case
Let’s walk through a hypothetical scenario where a user says to your AI voice service:
“AI, please create a new ticket for John about resetting his password.”

Flow:

Speech-to-Intent: Your AI converts the voice command to structured data:

Action: “create ticket”
User name: “John”
Subject: “Password reset request”
Message content: (optional) “John forgot his password.”
Check if “John” exists in Kayako:

AI calls GET /users?search=john@example.com (or uses a known user ID if you have it).
If not found, the AI can ask more questions (“Is this user new? Should I create them?”).
Create the conversation:

POST /conversations with:
json
Copy
{
  "subject": "Password reset request",
  "channel": "Voice",
  "requester": { "id": <johns_user_id> },
  "messages": [
    {
      "type": "reply",
      "content": "User requested a password reset via voice assistant."
    }
  ]
}
AI Reads Response:

The AI receives a conversation ID from Kayako, then it can say: “Ticket #XXXX has been created for John with the subject ‘Password reset request.’”
Future Voice Commands: The user might later say, “AI, check the status of John’s password reset ticket.”

AI finds the conversation ID and calls GET /conversations/{conversation_id}. It reads the status field and any new messages, then reports back: “That ticket is still open. The last agent note says: ‘Working on it now.’”
12. Additional Considerations
Webhooks: Kayako can optionally send outbound webhooks (if configured) when certain events happen (e.g., new conversation, conversation updated). If your voice service or AI agent can handle push events, you might use webhooks to proactively notify the user of updates.
Agents vs. End-Users: Depending on roles, you might have separate endpoints or permissions. Make sure your API key or OAuth credentials have the correct permission scope.
Attachments: You can upload attachments or retrieve them, but that typically requires a separate endpoint or a multi-part form POST to attach files to conversations.
13. Summary
Kayako’s REST API is a comprehensive, JSON-based interface for creating and managing conversations (tickets), users, organizations, and more. Integrating this with a voice service typically involves:

Parsing spoken requests into structured data.
Making the appropriate REST calls (with the correct JSON body).
Handling responses in real-time (reading them back to the user).
Handling authentication tokens and potential errors.
By following the endpoints and best practices outlined above, you can seamlessly tie Kayako’s helpdesk functionality into a voice-powered workflow—enabling your AI agent to create, search, update, and retrieve tickets using natural spoken commands.

Official Documentation
While the above should give you a very strong start, always consult Kayako’s official API documentation for your specific Kayako version. Different Kayako deployments (Cloud vs. On-Premise, Classic vs. New platform) may have slight variations in endpoints, parameters, or authentication flows.

Reference:

Kayako Official Docs – For the most up-to-date and specific details.
This concludes the in-depth overview of how Kayako’s API works and how to integrate it into a voice-based AI service. If you follow these guidelines and examples, your agent should be well-equipped to interact with Kayako’s system reliably and securely.