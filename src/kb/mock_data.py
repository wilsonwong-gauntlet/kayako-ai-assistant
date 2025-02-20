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
    },
    {
        "id": "art-004",
        "title": "Accepted Payment Methods",
        "content": """
We accept the following payment methods:
1. Credit/Debit Cards
   - Visa
   - Mastercard
   - American Express
2. Digital Wallets
   - PayPal
   - Apple Pay
   - Google Pay
3. Bank Transfer (ACH)

All payments are processed securely through our payment provider Stripe.
        """.strip(),
        "tags": ["payment", "billing", "credit card", "paypal"],
        "category": "Billing"
    },
    {
        "id": "art-005",
        "title": "Update Payment Information",
        "content": """
To update your payment method:
1. Log into your account
2. Go to Settings > Billing
3. Click 'Update Payment Method'
4. Enter new payment details
5. Click 'Save Changes'

Your next billing cycle will use the new payment method.
For help, contact support@example.com
        """.strip(),
        "tags": ["payment", "billing", "update", "settings"],
        "category": "Billing"
    },
    {
        "id": "art-006",
        "title": "Subscription Plans and Features",
        "content": """
Available subscription plans:

Basic Plan ($10/month):
- Up to 100 tickets/month
- Email support
- Basic reporting

Professional Plan ($25/month):
- Unlimited tickets
- Priority email & phone support
- Advanced reporting
- Custom branding

Enterprise Plan ($50/month):
- All Professional features
- 24/7 priority support
- API access
- Dedicated account manager

To upgrade/downgrade:
1. Go to Settings > Subscription
2. Choose new plan
3. Confirm changes
        """.strip(),
        "tags": ["subscription", "plans", "pricing", "features"],
        "category": "Billing"
    }
]

SAMPLE_TICKETS = [
    {
        "id": "tick-001",
        "subject": "Cannot access account",
        "contents": "Getting error when trying to log in",
        "channel": "phone",
        "channel_id": 1,
        "type_id": 1,
        "priority_id": 1,
        "status": "ACTIVE"
    }
]

# Status options for tickets
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]

# Priority options for tickets
TICKET_PRIORITIES = ["low", "medium", "high", "urgent"] 