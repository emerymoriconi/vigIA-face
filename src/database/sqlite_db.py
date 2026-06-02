import sqlite3
import time
import uuid
import os
import cv2
import logging
from src.config import DB_FILE, HISTORY_IMAGES_DIR

logger = logging.getLogger("AUDITORIA")

def init_db():
    """Inicializa SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id TEXT PRIMARY KEY,
            timestamp REAL,
            image_url TEXT,
            nome_completo TEXT,
            cpf TEXT,
            data_nascimento TEXT,
            ia_prob REAL,
            camera_id TEXT,
            sincronizado INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            filename TEXT,
            status TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cpf ON history(cpf)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time ON history(timestamp)')
    conn.commit()
    conn.close()

def log_backup(filename, status="success"):
    """Registra backup."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO backups (timestamp, filename, status) VALUES (?, ?, ?)', 
                       (time.time() * 1000, filename, status))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao logar backup: {e}")

def save_to_history(metadata, full_frame, last_history_save, cooldown):
    """Salva detecção e imagem."""
    try:
        person_key = metadata.get("cpf") or metadata.get("nome_completo")
        now = time.time()
        
        if person_key in last_history_save:
            if now - last_history_save[person_key] < cooldown:
                return None 
        
        det_id = str(uuid.uuid4())
        img_name = f"{det_id}.jpg"
        img_path = os.path.join(HISTORY_IMAGES_DIR, img_name)
        
        cv2.imwrite(img_path, full_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (id, timestamp, image_url, nome_completo, cpf, data_nascimento, ia_prob, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            det_id, 
            now * 1000, 
            f"/history_images/{img_name}",
            metadata["nome_completo"],
            metadata["cpf"],
            metadata["data_nascimento"],
            metadata["ia_prob"],
            metadata["camera_id"]
        ))
        conn.commit()
        conn.close()
            
        last_history_save[person_key] = now
        return {"id": det_id}
    except Exception as e:
        logger.error(f"Falha ao salvar histórico no SQLite: {e}")
        return None
