# User Guide

Complete guide to using BridgeAI.

## Getting Started

### 1. Sign Up / Login

1. Navigate to `http://localhost:3004` (or production URL)
2. Click **Sign Up** to create an account
3. Enter your email and password (minimum 8 characters)
4. You'll be automatically logged in

### 2. Connect Integrations

Before using BridgeAI, connect your business tools:

#### HubSpot CRM

1. Go to **Integrations** page
2. Click **Connect** next to HubSpot
3. Authorize BridgeAI in HubSpot
4. You'll be redirected back with a success message

#### Google (Gmail + Calendar)

1. Go to **Integrations** page
2. Click **Connect** next to Google
3. Authorize BridgeAI for Gmail and Calendar access
4. Both integrations will be connected

#### Discord (Optional)

Discord integration uses a bot token configured by administrators. No user action required.

## Using the Chat Interface

### Starting a Conversation

1. Navigate to **Chat** page
2. Type your message in the input box
3. Press **Enter** or click **Send**

### Example Queries

#### Single-Step Operations

| Query                                         | What It Does                       |
| --------------------------------------------- | ---------------------------------- |
| `Search for contacts in HubSpot`              | Finds contacts matching your query |
| `Show me recent emails`                       | Lists recent Gmail messages        |
| `What's on my calendar today?`                | Shows today's calendar events      |
| `Create a calendar event for tomorrow at 2pm` | Creates a new event                |
| `Send an email to john@example.com`           | Composes and sends email           |

#### Multi-Step Workflows

| Query                                        | Workflow                                                              |
| -------------------------------------------- | --------------------------------------------------------------------- |
| `Find contact John and send them an email`   | 1. Search HubSpot → 2. Extract email → 3. Send email                  |
| `Summarize my meetings and create CRM notes` | 1. List events → 2. Read transcripts → 3. Summarize → 4. Create notes |
| `Check calendar and send meeting reminders`  | 1. List upcoming events → 2. Extract attendees → 3. Send emails       |

### Conversation Management

- **New Conversation**: Click **New Chat** to start fresh
- **Previous Conversations**: Click on a conversation in the sidebar to resume
- **Session Persistence**: Conversations are automatically saved

## Integration Features

### HubSpot CRM

**Available Operations:**

- Search contacts and companies
- Update contact properties
- Create notes and tasks
- View deal information

**Example Queries:**

- `Search for contacts with email containing "gmail"`
- `Update contact 123 with email test@example.com`
- `Create a note for contact 456 about our meeting`

### Gmail

**Available Operations:**

- Read recent emails
- Send new emails
- Reply to emails
- Search emails

**Example Queries:**

- `Show me emails from last week`
- `Send an email to john@example.com with subject "Meeting" and body "Let's meet tomorrow"`
- `Reply to email [message_id]`

### Google Calendar

**Available Operations:**

- List events (today, this week, etc.)
- Create events
- Update events
- Delete events
- Get event details

**Example Queries:**

- `What meetings do I have today?`
- `Create a meeting tomorrow at 2pm with John`
- `Update meeting [event_id] to start at 3pm`
- `Cancel meeting [event_id]`

### Google Drive

**Available Operations:**

- List transcript files
- Read transcript files
- Create formatted documents
- Manage files and folders

**Example Queries:**

- `List all transcript files`
- `Read transcript file [file_id]`
- `Create a document with meeting summary`

### Meeting Analysis

**Available Operations:**

- Read meeting transcripts
- Summarize meetings
- Extract action items

**Example Queries:**

- `Read meeting transcript for event [event_id]`
- `Summarize the meeting from event [event_id]`
- `Extract action items from meeting [event_id]`

### Discord

**Available Operations:**

- Send messages to channels
- Read messages from channels
- List available channels

**Example Queries:**

- `Send a message to Discord channel [channel_id]`
- `Read messages from channel [channel_id]`
- `List Discord channels in server [guild_id]`

## Tips & Best Practices

### 1. Be Specific

✅ **Good**: "Search for contacts with email containing 'gmail.com'"
❌ **Vague**: "Find contacts"

### 2. Use Natural Language

BridgeAI understands natural language. You don't need to use specific commands.

✅ **Good**: "Create a calendar event for tomorrow at 2pm with John"
❌ **Too Technical**: "create_event start=2025-01-02T14:00"

### 3. Multi-Step Workflows

Break complex tasks into steps, or describe the full workflow:

✅ **Good**: "Find contact John, update his email to john@newcompany.com, and send him a welcome email"

### 4. Error Handling

If a tool fails:

- BridgeAI will explain what went wrong
- Check if the integration is still connected
- Verify you have the correct IDs (contact_id, event_id, etc.)

### 5. Session Management

- Each conversation has a unique `session_id`
- Previous context is maintained within a session
- Start a new conversation for unrelated topics

## Troubleshooting

### Integration Not Working

1. Check integration status on **Integrations** page
2. If disconnected, click **Connect** again
3. Verify OAuth permissions in provider settings

### Agent Not Responding

1. Check if you're logged in (token might be expired)
2. Refresh the page
3. Check browser console for errors

### Tool Execution Errors

Common errors and solutions:

| Error                 | Solution                                   |
| --------------------- | ------------------------------------------ |
| `401 Unauthorized`    | Reconnect the integration                  |
| `404 Not Found`       | Verify the ID (contact_id, event_id, etc.) |
| `Rate Limit Exceeded` | Wait a moment and try again                |
| `Invalid Input`       | Check the format of your request           |

## Keyboard Shortcuts

- **Enter**: Send message
- **Shift + Enter**: New line in message
- **Escape**: (Future) Cancel current operation

## Privacy & Security

- **Token Storage**: OAuth tokens are encrypted in the database
- **Conversation History**: Stored securely, only accessible by you
- **Data Access**: BridgeAI only accesses data you explicitly authorize
- **Token Refresh**: Automatic token refresh before expiry

## Getting Help

- Check the **API Documentation** for technical details
- Review **Architecture** docs for system understanding
- Check integration status on **Integrations** page
