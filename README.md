# BridgeAI

**AI Integration Copilot** - Production-ready AI assistant that integrates with business tools (CRM, email, calendar, team chat) to automate sales and operations workflows.

## 🎯 What is BridgeAI?

BridgeAI is an intelligent assistant that connects your business tools (HubSpot, Gmail, Google Calendar, Discord) and automates repetitive tasks. Instead of manually switching between apps, you simply ask BridgeAI what you need, and it handles the rest.

## ✨ Key Features

- **Multi-Tool Integration**: Seamlessly connects HubSpot, Gmail, Google Calendar, and Discord
- **AI-Powered Workflows**: Handles complex multi-step tasks automatically
- **Human-in-the-Loop**: Asks for approval before making important changes
- **Production-Ready**: Built with security, error handling, and observability in mind
- **Open Source**: Free and open-source portfolio project

## 🏗️ Tech Stack

- **Backend**: Python 3.12+ with FastAPI, LangGraph, LangChain
- **Frontend**: Next.js 14+ with TypeScript
- **Database**: PostgreSQL
- **Package Managers**: `uv` (Python), `pnpm` (Frontend)
- **Deployment**: Vercel (Frontend) + Railway (Backend)

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose

### Local Development (Docker-Only)

All development runs in Docker containers. No local Python or Node.js needed.

```bash
# 1. Clone repository
git clone https://github.com/StephaneWamba/bridge-ai.git
cd bridge-ai
git checkout develop

# 2. Set up environment variables
cd backend && cp .env.example .env && cd ..
cd frontend && cp .env.example .env.local && cd ..

# 3. Start all services
docker-compose up -d

# 4. Run database migrations
docker-compose exec backend alembic upgrade head

# 5. Access services
# Frontend: http://localhost:3004
# Backend API: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

**Hot Reload**: Both backend and frontend support hot reload - changes automatically restart/refresh.

See [private/project-roadmap.md](private/project-roadmap.md) for detailed setup instructions.

## 📚 Documentation

- [Project Roadmap](private/project-roadmap.md)
- [Project Scope & Objectives](private/project-scope-and-objectives.md)
- [Tech Stack Recommendation](private/tech-stack-recommendation.md)

## 📄 License

MIT License - See LICENSE file for details

---

**Status**: In Development  
**Branch**: `develop` (default)

