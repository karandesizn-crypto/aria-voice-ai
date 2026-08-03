from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app import __version__
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger, new_request_id, request_id_ctx
from app.infrastructure.db.session import create_engine, create_session_factory
from app.infrastructure.memory.embeddings import HashEmbeddingProvider, OpenAIEmbeddingProvider
from app.infrastructure.memory.store import PostgresMemoryStore
from app.infrastructure.redis.client import SessionCache, create_redis
from app.infrastructure.tools.factory import build_tools
from app.infrastructure.tools.registry import PostgresPermissionStore, ToolRegistry
from app.services.analytics_service import AnalyticsService
from app.services.graph_service import KnowledgeGraphService
from app.services.memory_service import MemoryService
from app.services.reminder_service import InProcessJobScheduler, ReminderService

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.environment)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1 if settings.environment == "production" else 0.0,
            integrations=[FastApiIntegration()],
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        http_client = httpx.AsyncClient(timeout=20.0)
        app.state.http_client = http_client

        engine = create_engine(settings)
        session_factory = create_session_factory(engine)
        redis_client = create_redis(settings)
        cache = SessionCache(redis_client)

        if settings.openai_api_key:
            embeddings = OpenAIEmbeddingProvider(
                api_key=settings.openai_api_key,
                model=settings.embedding_model,
                dimensions=settings.embedding_dimensions,
                http_client=http_client,
            )
        else:
            embeddings = HashEmbeddingProvider(settings.embedding_dimensions)
            logger.warning("embedding_fallback_hash", reason="OPENAI_API_KEY missing")

        memory_store = PostgresMemoryStore(session_factory, embeddings)
        app.state.memory_service = MemoryService(memory_store, cache)
        app.state.tool_registry = ToolRegistry(
            tools=build_tools(settings, http_client),
            permissions=PostgresPermissionStore(session_factory),
            cache=cache,
            session_factory=session_factory,
        )
        app.state.graph_service = KnowledgeGraphService(session_factory)
        scheduler = InProcessJobScheduler()
        app.state.reminder_service = ReminderService(session_factory, scheduler)
        app.state.analytics_service = AnalyticsService(session_factory)
        app.state.db_engine = engine
        app.state.redis = redis_client

        logger.info("api_startup", version=__version__, environment=settings.environment)
        try:
            yield
        finally:
            await http_client.aclose()
            await redis_client.aclose()
            await engine.dispose()
            logger.info("api_shutdown")

    app = FastAPI(
        title="Voice AI Platform API",
        version=__version__,
        description="Control plane for voice sessions, memory, and tools.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-User-Id"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        token = request_id_ctx.set(request_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)

    app.include_router(api_router)
    return app


app = create_app()
