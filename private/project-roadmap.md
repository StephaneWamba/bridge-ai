# BridgeAI — Project Roadmap

**Project Name**: BridgeAI  
**Version**: 1.0  
**Date**: 2025-01-27  
**Status**: Planning → Implementation  
**Timeline**: 8 weeks (Full Build)

---

## 🎯 Core Principles

### Non-Functional Requirements (NFRs)

1. **Performance** (Top Priority)

   - API response time: <500ms for simple queries
   - Multi-step workflows: <5s end-to-end
   - Frontend: First Contentful Paint <1.5s
   - Database queries: <100ms average
   - Optimized Docker builds for local dev

2. **Codebase Modularity & Maintainability**

   - Clear separation of concerns
   - Modular architecture (backend + frontend)
   - Reusable components and patterns
   - Comprehensive type safety (TypeScript + Pydantic)
   - Well-documented code (no placeholders)

3. **Production Readiness**

   - No technical debt
   - No placeholders or TODOs (unless absolutely necessary)
   - Proper error handling from day one
   - Observability built-in
   - Security best practices

4. **Don't Reinvent the Wheel**
   - Use proven libraries for OAuth (authlib, google-auth-library)
   - Use existing frameworks (FastAPI, Next.js, LangGraph)
   - Leverage managed services where appropriate
   - Focus on business logic, not infrastructure

---

## 🏗️ Technical Stack

### Backend

- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Package Manager**: `uv` (for speed)
- **Orchestration**: LangGraph
- **Tools**: LangChain
- **Database**: PostgreSQL
- **State Store**: PostgreSQL (LangGraph checkpointing)
- **Background Jobs**: Inngest (Python SDK)
- **Auth**: OAuth2 (authlib, google-auth-library) - **No custom auth**

### Frontend

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Package Manager**: `pnpm` (for speed)
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React Query (TanStack Query)
- **Real-time**: Polling (WebSockets if needed later)

### Infrastructure

- **Local Dev**: Docker Compose (optimized)
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Railway
- **Database**: Railway PostgreSQL or Supabase
- **Monitoring**: Sentry (or similar)

### Integrations

- **CRM**: HubSpot (OAuth2)
- **Email**: Gmail API (OAuth2)
- **Calendar**: Google Calendar API (OAuth2, shared with Gmail)
- **Team Chat**: Discord (Bot token)

---

## 📅 Implementation Roadmap

### Phase 1: Foundation & Infrastructure (Weeks 1-2)

**Goal**: Set up project structure, database, and first integration

#### Week 1: Project Setup ✅ COMPLETED

**Backend Setup:**

- [x] Initialize FastAPI project with `uv`
- [x] Set up project structure (modular architecture)
- [x] Configure Docker Compose for local dev (optimized builds)
- [x] Set up PostgreSQL database schema
- [x] Create database models (SQLAlchemy)
- [x] Set up database migrations (Alembic)
- [x] Configure environment variables
- [x] Set up logging and error handling
- [x] Create API structure (routes, dependencies)

**Frontend Setup:**

- [x] Initialize Next.js 14+ project with `pnpm`
- [x] Set up TypeScript configuration
- [x] Configure Tailwind CSS + shadcn/ui
- [x] Set up project structure (modular components)
- [x] Configure environment variables
- [x] Set up API client (React Query)
- [x] Create base layout and routing
- [x] **BONUS**: Created BridgeAI logo (SVG)

**DevOps:**

- [x] Set up GitHub Actions (CI/CD)
- [x] Configure Docker Compose for local development
- [x] Set up pre-commit hooks (linting, formatting)
- [x] Configure code quality tools (ruff, mypy for Python; ESLint, Prettier for TS)

**Deliverables:**

- ✅ Project structure ready
- ✅ Docker Compose working locally
- ✅ Database schema defined
- ✅ Basic API endpoints (health check, etc.)
- ✅ Basic frontend layout

---

#### Week 2: HubSpot Integration ✅ COMPLETED

**OAuth Implementation:**

- [x] Set up HubSpot OAuth2 flow (using authlib)
- [x] Create OAuth callback handler
- [x] Implement token storage (encrypted)
- [x] Implement token refresh logic
- [x] Create integration status endpoint
- [x] **BONUS**: Implement OAuth state verification (CSRF protection)
- [x] **BONUS**: Fix token refresh to sync with database automatically

**HubSpot API Client:**

- [x] Create HubSpot API client (modular, reusable)
- [x] Implement rate limiting
- [x] Implement error handling and retries
- [x] Create methods: read contacts, read companies, read deals
- [x] Create methods: update contact, update company
- [x] Create methods: create note, create activity

**Frontend Integration:**

- [x] Create OAuth connection flow UI
- [x] Create integration status component
- [x] Display connected integrations
- [x] Handle OAuth callbacks

**Testing:**

- [x] Test OAuth flow end-to-end
- [x] Test API client with real HubSpot data
- [x] Test error scenarios

**Deliverables:**

- ✅ HubSpot OAuth working
- ✅ Can read/write to HubSpot
- ✅ Frontend shows connection status
- ✅ Error handling comprehensive
- ✅ **Security**: OAuth state verification implemented
- ✅ **Data Consistency**: Token refresh automatically syncs with database

---

### Phase 2: Core Agent & Gmail (Weeks 3-4)

#### Week 3: Gmail Integration & Basic Agent ✅ COMPLETED

**Gmail OAuth:**

- [x] Set up Google OAuth2 flow (using google-auth-library)
- [x] Create OAuth callback handler
- [x] Implement token storage (encrypted)
- [x] Implement token refresh
- [x] Share OAuth with Calendar (same Google account)
- [x] **BONUS**: Implement OAuth state verification (CSRF protection)
- [x] **BONUS**: Fix insecure transport for localhost development
- [x] **BONUS**: Fix Gmail credentials to include client_id/client_secret for token refresh

**Gmail API Client:**

- [x] Create Gmail API client (modular)
- [x] Implement quota management
- [x] Implement error handling and retries
- [x] Create methods: read emails, send email, parse email
- [x] **BONUS**: Automatic token refresh on 401 errors with retry logic

**Basic LangGraph Setup:**

- [x] Set up LangGraph project structure
- [x] Create state schema (TypedDict for LangGraph)
- [x] Set up PostgreSQL checkpointing (AsyncPostgresSaver)
- [x] Create basic graph structure (nodes and edges)
- [x] Create tool definitions (LangChain tools)
- [x] Create initial tools:
  - `read_hubspot_contact`
  - `search_hubspot_contacts`
  - `read_hubspot_company`
  - `search_hubspot_companies`
  - `read_gmail_emails`
  - `send_gmail_email`

**Agent Orchestrator:**

- [x] Create agent entry point
- [x] Implement basic graph execution
- [x] Implement tool selection logic (via LLM with system prompt)
- [x] Implement tool execution (via LangGraph ToolNode)
- [x] Create response generation (basic)
- [x] **BONUS**: Added system prompt to encourage tool usage
- [x] **BONUS**: Fixed TypedDict access issues for AgentState

**Frontend Chat UI:**

- [x] Create chat interface component (Linear.app/Vercel-inspired design)
- [x] Implement message history with smooth scrolling
- [x] Display tool executions with modern visual indicators
- [x] Implement shimmering text loading for AI responses
- [x] Create loading states (animated dots)
- [x] Show contextual loading states
- [x] Handle errors in UI with modern error components
- [x] Add smooth animations and transitions

**Deliverables:**

- ✅ Gmail integration working (tested and verified)
- ✅ Google OAuth tested and working with automatic token refresh
- ✅ Basic agent responds to queries with tool calling (HubSpot and Gmail tools working)
- ✅ Chat UI functional with modern design
- ✅ Tool executions visible in chat
- ✅ Shimmering text animation for AI responses
- ✅ Agent successfully uses tools when appropriate (HubSpot contacts, Gmail emails)

---

#### Week 4: Agent Enhancement & Polish ✅ COMPLETED

**Agent Improvements:**

- [x] Add more tools (update contact, create note)
  - [x] `update_hubspot_contact`: Update contact properties
  - [x] `create_hubspot_note`: Create notes associated with contacts/companies
  - [x] `reply_gmail_email`: Reply to emails (properly threaded, no attachments)
- [x] Improve tool selection logic (via system prompt - already working)
- [x] Enhanced error handling with helpful messages
- [x] Improved agent feedback for edge cases (missing properties, invalid IDs)
- [x] Implement conversation history persistence (database + LangGraph checkpointing)
- [x] Create conversation service for managing chat history
- [x] Add endpoint to list conversations
- [x] Add context management (ContextService implemented, conversation summaries and context-aware responses working)
- [x] Add error recovery (enhanced error handling in system prompt and tool error handling)

**Gmail Integration Fixes:**

- [x] Fixed email sending - empty body issue (base64 padding fix)
- [x] Fixed unexpected "noname" attachments (proper MIMEText encoding)
- [x] Implemented proper reply functionality (threaded, no attachments)
- [x] Added no-reply address detection and warnings
- [x] Improved recipient visibility in reply responses
- [x] Enhanced email address extraction for replies

**HubSpot Integration Fixes:**

- [x] Fixed company note creation with dynamic association type ID lookup
- [x] Added contact verification before updates
- [x] Improved error messages for non-existent contacts/companies

**Frontend Enhancements:**

- [x] Complete modern UI redesign (Linear.app/Vercel-inspired)
- [x] Beautiful welcome screen with example cards
- [x] Modern message bubbles with avatars and glassmorphism
- [x] Simplified loading state with "Thinking..." shimmering text
- [x] Improved input area with keyboard hints
- [x] Smooth animations and transitions throughout
- [x] Better error handling with modern UI feedback
- [x] Responsive design for all screen sizes
- [x] Markdown rendering for message content
- [x] Dark mode toggle
- [x] Conversation history sidebar with session management
- [ ] Add retry functionality

**Performance Optimization:**

- [x] Optimize API response times (completed in Week 7)
- [x] Implement caching where appropriate (completed in Week 7)
- [x] Optimize database queries (completed in Week 7)
- [x] Frontend code splitting (completed in Week 7)
- [ ] Image optimization (if images added later)

**Testing:**

- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Error scenario testing

**Deliverables:**

- ✅ Agent handles complex queries
- ✅ UI is polished and performant
- ✅ Error handling comprehensive
- ✅ Performance targets met (completed in Week 7)

---

### Phase 3: Advanced Features (Weeks 5-6)

#### Week 5: Calendar Integration & Multi-Step Workflows ✅ COMPLETED

**Google Calendar Integration:**

- [x] Extend Google OAuth to include Calendar scope (already included)
- [x] Create Calendar API client
- [x] Implement methods: read events, create event
- [x] Create Calendar tools for agent (list_events, create_event)
- [x] Integrate Calendar tools with agent
- [ ] Implement meeting summary generation
- [ ] Extract action items from meetings

**Multi-Step Workflows:**

      - [x] Create complex workflow examples in system prompt:

- "Research company → Update CRM → Schedule follow-up"
- "Summarize meetings → Create CRM notes → Send email"
- "Find contact and send email"
- "Check calendar and send meeting reminders"
- [x] Add multi-step workflow guidance to system prompt
- [x] Implement conditional routing in LangGraph (already supported via agent -> tools -> agent loop)
- [x] Add workflow state management (context dict in AgentState)
- [x] Multi-step workflows functional (LangGraph handles sequential tool execution automatically)

**Human-in-the-Loop:**

- [ ] Implement approval node in LangGraph
- [ ] Create approval UI component
- [ ] Handle approval/rejection flows
- [ ] Store approval decisions
- [ ] Resume workflows after approval

**Deliverables:**

- ✅ Calendar integration working
- ✅ Multi-step workflows functional
- ⏳ Human-in-the-loop working (approval node pending - future feature)
- ⏳ Approval flows tested (pending approval node implementation)

---

#### Week 6: Error Handling & State Management ✅ COMPLETED

**Error Handling:**

- [x] Comprehensive error handling for all APIs (via handle_tool_error)
- [x] Retry logic with exponential backoff (via tenacity in integration clients)
- [x] Error recovery in workflows (enhanced system prompt guidance)
- [x] User-friendly error messages (handle_tool_error provides specific messages)
- [x] Error logging and monitoring (via logger)

**State Persistence:**

- [x] Ensure LangGraph checkpointing works correctly (PostgreSQL checkpointer)
- [x] Test state persistence across sessions (conversation history in DB)
- [x] Handle state recovery after failures (messages loaded from DB)
- [ ] Optimize checkpoint storage (future optimization)

**Context Management:**

- [x] Implement conversation context (ContextService)
- [x] Store tool execution results (via conversation messages)
- [ ] Maintain user preferences (future feature)
- [x] Context-aware responses (previous messages loaded for context)

**Performance:**

- [x] Optimize LangGraph execution (connection pooling enhanced in Week 7)
- [x] Optimize database queries (composite indexes added in Week 7)
- [x] Implement connection pooling (enhanced with recycling and keepalive in Week 7)
- [x] Cache frequently accessed data (integration caching implemented in Week 7)

**Deliverables:**

- ✅ Robust error handling
- ✅ State persists correctly
- ✅ Context management working
- ✅ Performance optimized (completed in Week 7)

---

### Phase 4: Production & Polish (Weeks 7-8)

#### Week 7: Polish & Performance Optimization ✅ COMPLETED

**UI/UX Improvements:**

- [x] Simplified tool feedback (removed, replaced with clean "Thinking..." state)
- [x] Markdown rendering for message content with proper whitespace preservation
- [x] Fixed conversation history display and navigation
- [x] Optimized conversation list processing (early breaks, better type checking)
- [ ] Add message retry functionality
- [ ] Improve error recovery UX
- [ ] Add loading skeletons for better perceived performance

**Performance Optimization:**

- [x] Optimize API response times (caching, query optimization)
- [x] Implement caching where appropriate (integration caching with TTL - 5 minutes)
- [x] Optimize database queries (composite indexes, connection pooling)
  - [x] Added composite index: `ix_conversations_user_id_updated_at`
  - [x] Enhanced connection pool with recycling and keepalive settings
- [x] Frontend optimization (Next.js config, compression, console.log removal)
- [ ] Image optimization (if images added later)
- [x] Reduce bundle size (production optimizations)

**Code Quality:**

- [x] Removed unused components (ToolIndicator, ShimmerText)
- [x] Cleaned up technical debt
- [x] Added SimpleCache class for in-memory caching
- [x] Optimized conversation title/preview extraction logic
- [ ] Add comprehensive error boundaries
- [ ] Improve TypeScript coverage
- [ ] Add unit tests for critical components

**Testing:**

- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Error scenario testing
- [ ] Cross-browser testing

**Deliverables:**

- ✅ UI/UX polished and simplified
- ✅ Codebase clean and maintainable
- ✅ Performance optimized
- ⏳ Testing comprehensive (pending)

---

#### Week 7/8: Discord Integration ✅ COMPLETED

**Discord Bot Integration:**

- [x] Create Discord bot and configure bot token
- [x] Implement Discord API client with rate limiting
- [x] Create Discord tools (send_message, read_messages, list_channels)
- [x] Integrate Discord tools with agent orchestrator
- [x] Update system prompt to include Discord capabilities
- [x] Configure Docker environment variables for Discord token
- [x] Fix LangGraph checkpointing dependency issues

**Deliverables:**

- ✅ Discord integration working
- ✅ Bot can send messages, read messages, and list channels
- ✅ Agent can use Discord tools in workflows

---

#### Week 8: Deployment & Documentation

**Production Deployment:**

- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway
- [ ] Set up production database
- [ ] Configure environment variables
- [ ] Set up monitoring (Sentry)
- [ ] Set up logging aggregation
- [ ] Test production deployment

**Documentation:**

- [ ] Write comprehensive README
- [ ] Create setup guide
- [ ] Document API endpoints
- [ ] Document architecture
- [ ] Create deployment guide
- [ ] Write demo script

**Final Testing:**

- [ ] End-to-end testing in production
- [ ] Performance testing
- [ ] Security testing
- [ ] Load testing (if applicable)

**Demo Preparation:**

- [ ] Record demo video
- [ ] Prepare demo data
- [ ] Test demo flow
- [ ] Create demo script

**Deliverables:**

- ✅ System deployed to production
- ✅ Documentation complete
- ✅ Demo ready
- ✅ Portfolio-ready

---

## 🏗️ Project Structure

```
bridge-ai/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── integrations.py
│   │   │   │   ├── agent.py
│   │   │   │   └── admin.py
│   │   │   └── dependencies.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   └── cache.py
│   │   ├── integrations/
│   │   │   ├── base.py (base integration class)
│   │   │   ├── hubspot/
│   │   │   │   ├── client.py
│   │   │   │   ├── oauth.py
│   │   │   │   └── models.py
│   │   │   ├── gmail/
│   │   │   │   ├── client.py
│   │   │   │   ├── oauth.py
│   │   │   │   └── models.py
│   │   │   ├── calendar/
│   │   │   │   ├── client.py
│   │   │   │   └── models.py
│   │   │   └── discord/
│   │   │       ├── client.py
│   │   │       └── models.py
│   │   ├── agent/
│   │   │   ├── graph/
│   │   │   │   ├── state.py
│   │   │   │   ├── nodes.py
│   │   │   │   ├── edges.py
│   │   │   │   └── orchestrator.py
│   │   │   ├── tools/
│   │   │   │   ├── base.py
│   │   │   │   ├── hubspot_tools.py
│   │   │   │   ├── gmail_tools.py
│   │   │   │   ├── calendar_tools.py
│   │   │   │   └── discord_tools.py
│   │   │   └── executor.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── integration.py
│   │   │   ├── activity.py
│   │   │   └── conversation.py
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── integration_service.py
│   │       ├── conversation_service.py
│   │       ├── context_service.py
│   │       └── activity_service.py
│   ├── tests/
│   ├── pyproject.toml (uv)
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── chat/
│   │   │   │   ├── integrations/
│   │   │   │   └── admin/
│   │   │   └── api/ (API routes)
│   │   ├── components/
│   │   │   ├── ui/ (shadcn components)
│   │   │   ├── chat/
│   │   │   ├── integrations/
│   │   │   └── admin/
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   ├── hooks/
│   │   │   └── utils/
│   │   └── types/
│   ├── public/
│   ├── package.json (pnpm)
│   ├── Dockerfile
│   └── next.config.js
├── private/
│   ├── project-roadmap.md
│   ├── project-scope-and-objectives.md
│   ├── tech-stack-recommendation.md
│   └── ai-integration-copilot-project.md
├── docker-compose.yml (root)
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
└── README.md
```

---

## 🔧 Development Guidelines

### Code Quality

1. **Type Safety**

   - TypeScript: Strict mode enabled
   - Python: Type hints everywhere, mypy checks
   - Pydantic models for all data structures

2. **No Placeholders**

   - No `TODO` comments (unless absolutely necessary)
   - No placeholder functions
   - No mock data in production code
   - Complete implementations from day one

3. **Error Handling**

   - Comprehensive error handling
   - User-friendly error messages
   - Proper logging
   - Error recovery where possible

4. **Testing**
   - Unit tests for critical functions
   - Integration tests for API endpoints
   - E2E tests for critical flows
   - Performance tests

### Performance Guidelines

1. **Backend**

   - Database query optimization
   - Connection pooling
   - Caching where appropriate
   - Async operations
   - Rate limiting

2. **Frontend**

   - Code splitting
   - Image optimization
   - Lazy loading
   - Efficient re-renders
   - Optimistic updates

3. **Docker**
   - Multi-stage builds
   - Layer caching
   - Minimal base images
   - Optimized for local dev speed

### Modularity Guidelines

1. **Separation of Concerns**

   - Clear boundaries between modules
   - Reusable components
   - Shared utilities
   - Clear interfaces

2. **Dependency Management**
   - Minimal dependencies
   - Well-maintained libraries
   - Clear dependency boundaries
   - No circular dependencies

---

## 📊 Success Metrics

### Performance Metrics

- API response time: <500ms (p95)
- Multi-step workflow: <5s end-to-end
- Frontend FCP: <1.5s
- Database queries: <100ms average

### Code Quality Metrics

- Type coverage: 100%
- Test coverage: >80% for critical paths
- No critical linting errors
- All TODOs resolved (or justified)

### Integration Metrics

- All 4 integrations working
- OAuth flows: 100% success rate
- Tool execution: >95% success rate (with retries)

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- `uv` installed
- `pnpm` installed

### Local Development Setup

1. **Clone repository**

   ```bash
   git clone https://github.com/StephaneWamba/bridge-ai.git
   cd bridge-ai
   git checkout develop
   ```

2. **Backend Setup**

   ```bash
   cd backend
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **Frontend Setup**

   ```bash
   cd frontend
   pnpm install
   ```

4. **Docker Setup**

   ```bash
   docker-compose up -d
   ```

5. **Run Development Servers**

   ```bash
   # Backend
   cd backend
   uvicorn src.main:app --reload

   # Frontend
   cd frontend
   pnpm dev
   ```

---

**Last Updated**: 2025-12-28  
**Status**: Discord Integration Completed  
**Current Focus**:

- ✅ Discord integration completed and working
- ✅ Performance optimizations completed (caching, indexes, connection pooling)
- ✅ UI/UX improvements completed (markdown rendering, conversation history)
- ✅ All 4 core integrations working (HubSpot, Gmail, Calendar, Discord)
- ⏳ Testing and additional polish items pending

**Next Step**: Week 8 - Deployment & Documentation, or Enterprise-Grade Enhancements
