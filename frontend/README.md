# BridgeAI Frontend

Next.js 14+ frontend for BridgeAI - AI Integration Copilot.

## Setup (Docker-Only Development)

### Prerequisites

- Docker & Docker Compose

### Local Development

All development is done in Docker containers. No local Node.js installation needed.

1. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

2. **Start all services (from project root):**
   ```bash
   docker-compose up -d
   ```

3. **Access frontend:**
   - Frontend: http://localhost:3004
   - Backend API: http://localhost:8001

## Development Commands

All commands run inside Docker containers:

- **View logs:**
  ```bash
  docker-compose logs -f frontend
  ```

- **Type checking:**
  ```bash
  docker-compose exec frontend pnpm type-check
  ```

- **Linting:**
  ```bash
  docker-compose exec frontend pnpm lint
  ```

- **Formatting:**
  ```bash
  docker-compose exec frontend pnpm format
  ```

- **Build:**
  ```bash
  docker-compose exec frontend pnpm build
  ```

- **Shell access:**
  ```bash
  docker-compose exec frontend /bin/sh
  ```

## Hot Reload

Frontend supports hot reload - changes to React/TypeScript files automatically refresh the browser.

## Design System

- **Theme**: Linear.app/Vercel-inspired minimalist design
- **Styling**: Tailwind CSS + shadcn/ui
- **Animations**: framer-motion
- **Loading States**: Shimmer/skeleton loaders

