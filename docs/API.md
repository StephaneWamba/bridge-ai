# API Documentation

Complete reference for BridgeAI REST API.

## Base URL

- **Development**: `http://localhost:8001`
- **Production**: Configured via environment variables

## Authentication

All endpoints (except `/api/v1/auth/*`) require JWT authentication.

**Header Format:**

```
Authorization: Bearer <access_token>
```

**Token Refresh:**

- Access tokens expire in 30 minutes
- Refresh tokens expire in 7 days
- Use `/api/v1/auth/refresh` to get new tokens

## Endpoints

### Authentication

#### `POST /api/v1/auth/signup`

Register a new user.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `POST /api/v1/auth/login`

Authenticate user.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `POST /api/v1/auth/refresh`

Refresh access token.

**Request:**

```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### `GET /api/v1/auth/me`

Get current user information.

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

### Integrations

#### `GET /api/v1/integrations/hubspot/authorize`

Initiate HubSpot OAuth flow.

**Response:** `200 OK`

```json
{
  "authorization_url": "https://app.hubspot.com/oauth/authorize?...",
  "state": "random-state-token"
}
```

#### `GET /api/v1/integrations/hubspot/callback`

OAuth callback (redirects to frontend).

**Query Parameters:**

- `code`: OAuth authorization code
- `state`: CSRF protection token

#### `GET /api/v1/integrations/hubspot/status`

Get HubSpot integration status.

**Response:** `200 OK`

```json
{
  "connected": true,
  "is_active": true,
  "expires_at": "2025-12-31T23:59:59",
  "working": true
}
```

#### `POST /api/v1/integrations/hubspot/disconnect`

Disconnect HubSpot integration.

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "HubSpot integration disconnected",
  "deleted": true
}
```

#### `GET /api/v1/integrations/google/authorize`

Initiate Google OAuth flow (Gmail + Calendar).

**Response:** `200 OK`

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random-state-token"
}
```

#### `GET /api/v1/integrations/google/callback`

OAuth callback (redirects to frontend).

#### `GET /api/v1/integrations/google/status`

Get Google integration status.

**Response:** `200 OK`

```json
{
  "gmail": {
    "connected": true,
    "is_active": true
  },
  "calendar": {
    "connected": true,
    "is_active": true
  }
}
```

#### `POST /api/v1/integrations/google/disconnect`

Disconnect Google integration.

### Agent

#### `POST /api/v1/agent/chat`

Process chat message (non-streaming).

**Request:**

```json
{
  "message": "Search for contacts in HubSpot",
  "session_id": "optional-session-id"
}
```

**Response:** `200 OK`

```json
{
  "response": "I found 5 contacts...",
  "session_id": "uuid",
  "tool_calls": [
    {
      "tool_name": "search_hubspot_contacts",
      "tool_input": { "query": "contacts" }
    }
  ]
}
```

#### `POST /api/v1/agent/chat/stream`

Process chat message (Server-Sent Events streaming).

**Request:**

```json
{
  "message": "Search for contacts in HubSpot",
  "session_id": "optional-session-id"
}
```

**Response:** `200 OK` (text/event-stream)

```
data: {"type": "response", "response": "I found 5 contacts...", "session_id": "uuid"}

data: {"type": "error", "error": "Error message"}
```

#### `GET /api/v1/agent/conversations`

List recent conversations.

**Query Parameters:**

- `limit`: Number of conversations (1-100, default: 20)

**Response:** `200 OK`

```json
{
  "conversations": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "title": "Search for contacts...",
      "preview": "I found 5 contacts...",
      "message_count": 4,
      "created_at": "2025-01-01T00:00:00",
      "updated_at": "2025-01-01T00:05:00"
    }
  ]
}
```

#### `GET /api/v1/agent/conversations/{session_id}/messages`

Get messages for a conversation.

**Response:** `200 OK`

```json
{
  "session_id": "uuid",
  "messages": [
    {
      "id": "uuid-0",
      "role": "user",
      "content": "Search for contacts",
      "timestamp": "2025-01-01T00:00:00"
    },
    {
      "id": "uuid-1",
      "role": "assistant",
      "content": "I found 5 contacts...",
      "tool_calls": [
        {
          "tool_name": "search_hubspot_contacts",
          "tool_input": { "query": "contacts" },
          "tool_id": "call_abc123"
        }
      ],
      "timestamp": "2025-01-01T00:00:05"
    }
  ]
}
```

### Health

#### `GET /health`

Health check endpoint.

**Response:** `200 OK`

```json
{
  "status": "healthy"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Status Codes:**

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

Currently no rate limiting. Consider implementing for production.

## WebSocket / SSE

The `/api/v1/agent/chat/stream` endpoint uses Server-Sent Events (SSE) for real-time streaming:

1. Client sends POST request with message
2. Server responds with `text/event-stream` content type
3. Server streams events as `data: <json>\n\n`
4. Client parses each event and updates UI

**Event Types:**

- `response` - Final agent response
- `error` - Error occurred
