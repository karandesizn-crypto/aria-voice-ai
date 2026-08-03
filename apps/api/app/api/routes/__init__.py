from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import graph, health, memory, phase4, reminders, tools, voice

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(voice.router)
api_router.include_router(memory.router)
api_router.include_router(tools.router)
api_router.include_router(graph.router)
api_router.include_router(reminders.router)
api_router.include_router(phase4.router)
