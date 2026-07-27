import os
import socket
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import logging

load_dotenv()

# Geral
VIGIA_API_KEY = os.getenv("VIGIA_API_KEY") or os.getenv("VITE_VIGIA_API_KEY")
VIGIA_MASTER_KEY = os.getenv("VIGIA_MASTER_KEY")
VIGIA_DEVICE_ID = os.getenv("VIGIA_DEVICE_ID", socket.gethostname())
ENABLE_DOCS = os.getenv("VIGIA_ENABLE_DOCS", "false").lower() == "true"
HISTORY_COOLDOWN = int(os.getenv("HISTORY_COOLDOWN", "60"))
AI_THRESHOLD = float(os.getenv("AI_THRESHOLD", "0.45"))

# Modelos
DETECTOR_MODEL = os.getenv("DETECTOR_MODEL", "./weights/det_10g.onnx")
RECOGNIZER_MODEL = os.getenv("RECOGNIZER_MODEL", "./weights/w600k_mbf.onnx")

# Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_PATH = os.getenv("QDRANT_PATH", "./database/face_database")
QDRANT_VOLUME_LIMIT_GB = float(os.getenv("QDRANT_VOLUME_LIMIT_GB", "5.0"))

# SQLite/Histórico
HISTORY_DIR = "./database/history"
HISTORY_IMAGES_DIR = os.path.join(HISTORY_DIR, "images")
DB_FILE = os.path.join(HISTORY_DIR, "history.db")
os.makedirs(HISTORY_IMAGES_DIR, exist_ok=True)

# Criptografia
cipher_suite = None
if VIGIA_MASTER_KEY:
    cipher_suite = Fernet(VIGIA_MASTER_KEY.encode())
else:
    logging.getLogger("AUDITORIA").error("VIGIA_MASTER_KEY não configurada.")
