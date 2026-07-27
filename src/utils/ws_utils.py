import asyncio
import logging
from src.core import state

logger = logging.getLogger("AUDITORIA")

async def broadcast_ws(message: str):
    """Broadcast WS."""
    for ws in list(state.active_connections):
        try:
            lock = state.connection_locks.get(ws)
            if lock:
                async with lock:
                    await ws.send_text(message)
        except Exception as e:
            logger.debug(f"Falha ao enviar WS para um cliente: {e}")

def broadcast_ws_sync(message: str):
    """Broadcast WS (síncrono)."""
    if state.loop and state.loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_ws(message), state.loop)
