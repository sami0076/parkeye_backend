import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, events, feedback, lots, predictions
from app.routers import websocket as ws_router
from app.routers.websocket import _broadcast_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Parkeye Backend",
        version="0.1.0",
        description="MVP backend for the Parkeye GMU parking app.",
        lifespan=lifespan,
    )

    origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(lots.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    app.include_router(events.router)
    app.include_router(feedback.router)
    app.include_router(ws_router.router)

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
