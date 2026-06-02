"""
FastAPI application factory for the Review Intelligence Platform.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from review_intel.config import get_settings

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = FastAPI(
        title="Review Intelligence Platform",
        description="WABA & SaaS customer intelligence from review data",
        version="2.0.0-alpha",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # V2 API routes
    from review_intel.api.routes import router as v2_router
    app.include_router(v2_router)

    # Legacy v1 routes (backward compatibility)
    try:
        from agent.routes import router as v1_router
        app.include_router(v1_router)
    except ImportError:
        pass

    # Gradio UI
    try:
        from review_intel.ui.gradio_app import create_gradio_app
        import gradio as gr
        gradio_blocks = create_gradio_app()
        app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")
    except Exception as e:
        logging.getLogger(__name__).warning("Gradio UI not loaded: %s", e)

    @app.get("/")
    async def root():
        return {
            "name": "Review Intelligence Platform",
            "version": "2.0.0-alpha",
            "docs": "/docs",
            "ui": "/gradio",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("review_intel.main:app", host=settings.host, port=settings.port, reload=False)
