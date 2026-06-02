import threading
import queue
from typing import Dict, List
from fastapi import WebSocket
import asyncio

# Conexões
inference_enabled = True
active_connections: List[WebSocket] = []
connection_locks: Dict[WebSocket, asyncio.Lock] = {}
inference_queue = queue.Queue(maxsize=1)
stop_event = threading.Event()
loop = None

# Detecção e Cache
latest_detections = []
detections_lock = threading.Lock()
last_history_save = {}  # Cache para controle de cooldown de histórico
last_ui_update = {}     # Cache para controle de cooldown de interface

# Instâncias Globais
detector = None
recognizer = None
face_db = None
camera = None
