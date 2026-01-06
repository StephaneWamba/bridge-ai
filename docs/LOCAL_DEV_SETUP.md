# Local Development Setup

Complete guide for setting up BridgeAI locally.

## Prerequisites

| Requirement        | Version | Purpose                       |
| ------------------ | ------- | ----------------------------- |
| **Docker**         | 20.10+  | Container runtime             |
| **Docker Compose** | 2.0+    | Multi-container orchestration |
| **Git**            | 2.30+   | Version control               |

**Note**: No local Python or Node.js installation required. Everything runs in Docker.

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/StephaneWamba/bridge-ai.git
cd bridge-ai
git checkout develop
```

### 2. Environment Variables

#### Backend Environment

Create `backend/.env`:

```bash
# Application
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-32-chars-minimum

# Database (Docker Compose handles connection)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/bridgeai
LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:postgres@postgres-checkpoints:5432/bridgeai_checkpoints

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# HubSpot OAuth
HUBSPOT_CLIENT_ID=your-hubspot-client-id
HUBSPOT_CLIENT_SECRET=your-hubspot-client-secret
HUBSPOT_REDIRECT_URI=http://localhost:8001/api/v1/integrations/hubspot/callback

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/integrations/google/callback

# Discord Bot (Optional)
DISCORD_BOT_TOKEN=your-discord-bot-token
```

#### Frontend Environment

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_ENV=development
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

## Service URLs

| Service            | URL                        | Purpose          |
| ------------------ | -------------------------- | ---------------- |
| **Frontend**       | http://localhost:3004      | Web interface    |
| **Backend API**    | http://localhost:8001      | REST API         |
| **API Docs**       | http://localhost:8001/docs | Swagger UI       |
| **PostgreSQL**     | localhost:5434             | Primary database |
| **Checkpoints DB** | localhost:5433             | LangGraph state  |

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: Changes to `.py` files trigger auto-reload
- **Frontend**: Changes to `.tsx`/`.ts` files trigger Next.js fast refresh

### Backend Development

```bash
# View backend logs
docker-compose logs -f backend

# Execute commands in backend container
docker-compose exec backend bash

# Run Python commands
docker-compose exec backend python -m src.main

# Run tests (when implemented)
docker-compose exec backend pytest
```

### Frontend Development

```bash
# View frontend logs
docker-compose logs -f frontend

# Execute commands in frontend container
docker-compose exec frontend sh

# Install new package
docker-compose exec frontend pnpm add package-name

# Run type check
docker-compose exec frontend pnpm type-check
```

## Database Management

### Accessing PostgreSQL

```bash
# Connect to primary database
docker-compose exec postgres psql -U postgres -d bridgeai

# Connect to checkpoints database
docker-compose exec postgres-checkpoints psql -U postgres -d bridgeai_checkpoints
```

### Common Database Operations

```sql
-- List all tables
\dt

-- View users
SELECT * FROM users;

-- View integrations
SELECT user_id, provider, is_active FROM integrations;

-- View conversations
SELECT session_id, created_at FROM conversations LIMIT 10;
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker-compose down -v

# Restart and migrate
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## OAuth Setup

### HubSpot OAuth

1. Go to [HubSpot Developer Portal](https://developers.hubspot.com/)
2. Create a new app
3. Add OAuth scopes:
   - `contacts.read`
   - `contacts.write`
   - `companies.read`
   - `companies.write`
   - `deals.read`
   - `deals.write`
4. Set redirect URI: `http://localhost:8001/api/v1/integrations/hubspot/callback`
5. Copy `Client ID` and `Client Secret` to `.env`

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable APIs:
   - Gmail API
   - Google Calendar API
   - Google Drive API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8001/api/v1/integrations/google/callback`
6. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive.readonly`
7. Copy `Client ID` and `Client Secret` to `.env`

### Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create bot and copy token
5. Add bot to your server with permissions:
   - Send Messages
   - Read Message History
   - Read Messages/View Channels
6. Copy token to `.env`

## Testing Integrations

### Test HubSpot Connection

1. Start services
2. Sign up/login at http://localhost:3004
3. Go to Integrations page
4. Click "Connect" for HubSpot
5. Authorize and verify status shows "Connected"

### Test Google Connection

1. Go to Integrations page
2. Click "Connect" for Google
3. Authorize Gmail and Calendar
4. Verify both show "Connected"

### Test Discord Bot

1. Ensure `DISCORD_BOT_TOKEN` is set
2. Check backend logs for "Discord bot logged in"
3. Send a DM to the bot or mention it in a channel
4. Bot should respond

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

### Database Connection Errors

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Check connection string in .env
# Should use service name: postgres:5432 (not localhost)
```

### Port Conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8002:8000" # Change 8001 to 8002
```

### Hot Reload Not Working

```bash
# Rebuild containers
docker-compose up -d --build

# Check volume mounts in docker-compose.yml
```

### Migration Errors

```bash
# Check current migration version
docker-compose exec backend alembic current

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

## Production Considerations

### Environment Variables

- Use strong `SECRET_KEY` and `ENCRYPTION_KEY`
- Set `DEBUG=false`
- Use production database URLs
- Configure CORS origins properly

### Security

- Never commit `.env` files
- Use secrets management (e.g., Railway, Vercel)
- Enable HTTPS in production
- Set proper CORS origins

### Performance

- Use connection pooling (already configured)
- Enable database query caching
- Monitor API response times
- Set up logging aggregation

## Next Steps

- Read [API Documentation](API.md) for endpoint details
- Review [Architecture](ARCHITECTURE.md) for system design
- Check [User Guide](USER_GUIDE.md) for usage examples
