"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import logger
from src.api.routes import health, integrations, agent, auth
from src.services.discord_bot import start_discord_bot, stop_discord_bot

app = FastAPI(
    title="BridgeAI API",
    description="AI Integration Copilot - Production-ready AI assistant",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(integrations.router)
app.include_router(agent.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("BridgeAI API starting up...")
    # Start Discord bot in background
    await start_discord_bot()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("BridgeAI API shutting down...")
    # Stop Discord bot
    await stop_discord_bot()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "BridgeAI API", "version": "0.1.0"}
