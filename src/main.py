import asyncio
import threading
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.core import state
from src.core.engine import init_engines, inference_worker
from src.api.stream import stream_frames_task, websocket_handler
from src.api.routes import router
from src.database.sqlite_db import init_db
from src.config import ENABLE_DOCS, HISTORY_IMAGES_DIR
from src.utils.logging import setup_logging

# Configuração de logs
setup_logging(level=logging.INFO, log_to_file=True, filename="logs/app.log")
logger = logging.getLogger("AUDITORIA")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida: inicializa DB, IA e threads."""
    init_db()
    init_engines()
    state.loop = asyncio.get_running_loop()
    
    # IA em thread dedicada
    ia_thread = threading.Thread(target=inference_worker, daemon=True)
    ia_thread.start()
    
    # Task streaming WS
    stream_task = asyncio.create_task(stream_frames_task())
    
    yield
    
    # Cleanup
    state.stop_event.set()
    stream_task.cancel()
    if state.camera:
        state.camera.stop()
    
    if hasattr(state, 'face_db') and state.face_db:
        state.face_db.close()
        
    ia_thread.join(timeout=2.0)

# FastAPI
docs_url = "/docs" if ENABLE_DOCS else None
app = FastAPI(lifespan=lifespan, docs_url=docs_url, redoc_url=docs_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/history_images", StaticFiles(directory=HISTORY_IMAGES_DIR), name="history_images")
app.include_router(router)
app.add_api_websocket_route("/ws", websocket_handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
