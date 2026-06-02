import logging
import threading
import webbrowser
from pathlib import Path

import gradio as gr
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent.routes import router as api_router
from agent.ui import create_gradio_app

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Review Scraper & Analyzer Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.include_router(api_router)

gradio_blocks = create_gradio_app()
app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")


@app.get("/")
async def root():
    return {"message": "Review Scraper Agent - Go to /gradio for the UI"}


def open_browser():
    webbrowser.open("http://127.0.0.1:8000/gradio")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
