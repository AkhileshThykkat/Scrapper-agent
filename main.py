import logging
import sys
import threading
import webbrowser
from pathlib import Path

# Ensure src/ is on the Python path for review_intel imports
_src = str(Path(__file__).parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

import gradio as gr
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Review Intelligence Platform", version="2.0.0-alpha")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")

# V1 legacy routes (backward compat)
try:
    from agent.routes import router as v1_router
    app.include_router(v1_router)
except Exception as e:
    logger.info("V1 routes not loaded: %s", e)

# V2 API routes
try:
    from review_intel.api.routes import router as v2_router
    app.include_router(v2_router)
    logger.info("V2 API routes loaded at /api/v2")
except Exception as e:
    logger.warning("V2 routes failed to load: %s", e)

# Mount Gradio UI — prefer v2, fall back to v1
try:
    from review_intel.ui.gradio_app import create_gradio_app
    gradio_blocks = create_gradio_app()
    app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")
    logger.info("V2 Gradio UI mounted at /gradio")
except Exception as e:
    logger.warning("V2 Gradio UI failed: %s — falling back to v1", e)
    try:
        from agent.ui import create_gradio_app
        gradio_blocks = create_gradio_app()
        app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")
        logger.info("V1 Gradio UI mounted at /gradio (fallback)")
    except Exception as e2:
        logger.error("No Gradio UI available: %s", e2)


@app.get("/")
async def root():
    return {
        "name": "Review Intelligence Platform",
        "version": "2.0.0-alpha",
        "docs": "/docs",
        "ui": "/gradio",
        "api_v2": "/api/v2/companies",
    }


def open_browser():
    webbrowser.open("http://127.0.0.1:8000/gradio")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
