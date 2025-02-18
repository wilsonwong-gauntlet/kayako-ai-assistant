"""Mock data for Kayako API development."""

SAMPLE_ARTICLES = [
    {
        "id": "art-001",
        "title": "How to Reset Your Password",
        "content": """
To reset your password:
1. Click on 'Forgot Password' link
2. Enter your email address
3. Check your email for reset instructions
4. Click the reset link and create a new password
        """.strip(),
        "tags": ["password", "account", "security"],
        "category": "Account Management"
    },
    {
        "id": "art-002",
        "title": "Billing Cycle Explained",
        "content": """
Our billing cycle runs monthly. Your subscription:
- Starts on sign up date
- Renews automatically each month
- Can be cancelled anytime
- Provides pro-rated refunds
        """.strip(),
        "tags": ["billing", "subscription", "payment"],
        "category": "Billing"
    },
    {
        "id": "art-003",
        "title": "Getting Started Guide",
        "content": """
Welcome to our service! Here's how to get started:
1. Create your account
2. Set up your profile
3. Configure your preferences
4. Start using the features
        """.strip(),
        "tags": ["onboarding", "setup", "getting started"],
        "category": "Getting Started"
    }
]

SAMPLE_TICKETS = [
    {
        "id": "tick-001",
        "subject": "Cannot access account",
        "description": "Getting error when trying to log in",
        "requester_email": "user@example.com",
        "phone_number": "+1234567890",
        "status": "open",
        "priority": "high"
    }
]

# Status options for tickets
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]

# Priority options for tickets
TICKET_PRIORITIES = ["low", "medium", "high", "urgent"] 