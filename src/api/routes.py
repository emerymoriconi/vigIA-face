import os
import time
import uuid
import hashlib
import json
import logging
import sqlite3
import zipfile
import cv2
import numpy as np
import psutil
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse, PlainTextResponse
from starlette.background import BackgroundTasks

from src.core import state
from src.core.security import get_api_key
from src.config import (
    VIGIA_API_KEY, DB_FILE, QDRANT_PATH, cipher_suite, HISTORY_IMAGES_DIR
)
from src.database.sqlite_db import log_backup
from src.utils.normalization import normalize_name, normalize_cpf, normalize_birth_date

router = APIRouter()
logger = logging.getLogger("AUDITORIA")

@router.get("/status")
async def get_status():
    cpu_usage = 0.0
    ram_percent = 0.0
    ram_available_mb = 0.0
    cpu_temp = 0.0
    
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_available_mb = round(ram.available / (1024*1024), 2)
        
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = int(f.read()) / 1000.0
            except Exception as e:
                logger.debug(f"Erro ao ler temperatura: {e}")
    except Exception as e:
        logger.error(f"Erro ao obter métricas de hardware: {e}")

    camera_active = False
    try:
        camera_active = state.camera.started if state.camera else False
    except:
        pass

    db_faces = 0
    try:
        db_faces = state.face_db.count_unique_people() if state.face_db else 0
    except Exception as e:
        logger.error(f"Erro ao contar faces: {e}")

    return {
        "status": "online",
        "camera_active": camera_active,
        "db_faces": db_faces,
        "hardware": {
            "cpu": cpu_usage,
            "ram_percent": ram_percent,
            "ram_available_mb": ram_available_mb,
            "temperature": cpu_temp
        }
    }

@router.get("/db_inspect", dependencies=[Depends(get_api_key)])
async def db_inspect():
    try:
        total_faces = state.face_db.count_unique_people() if state.face_db else 0
        people = state.face_db.get_all_people()
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM backups ORDER BY timestamp DESC LIMIT 10')
        rows = cursor.fetchall()
        backups = [dict(row) for row in rows]
        conn.close()
        return {"total": total_faces, "people": people, "backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register", dependencies=[Depends(get_api_key)])
async def register_face(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    nome: str = Form(...),
    cpf: str = Form(...),
    nascimento: str = Form(...)
):
    try:
        nome = normalize_name(nome)
        cpf = normalize_cpf(cpf)
        nascimento = normalize_birth_date(nascimento)

        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None: raise HTTPException(status_code=400, detail="Imagem inválida")
        
        bboxes, kpss = state.detector.detect(image, max_num=1)
        if kpss is None or len(kpss) == 0: raise HTTPException(status_code=400, detail="Nenhum rosto detectado")
        
        timestamp_suffix = int(time.time())
        embedding = np.array(state.recognizer.get_embedding(image, kpss[0]), dtype=np.float32)
        
        formatted_name = f"{cpf}|{nome}|{nascimento}|{timestamp_suffix}"
        
        # Payload estruturado compatível com o snapshot original
        payload = {
            "person_id": cpf,
            "name": formatted_name,  # Mantém compatibilidade com logs/UI antiga se necessário
            "metadata": {
                "id": cpf,
                "source": "Local",
                "name": nome,
                "birthdate": nascimento,
                "cpf": cpf
            },
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        }
        
        state.face_db.add_faces_batch([embedding], [payload])
        
        cpf_hash = hashlib.md5(cpf.encode('utf-8')).hexdigest()
        faces_dir = os.path.join("./assets/faces", cpf_hash)
        os.makedirs(faces_dir, exist_ok=True)
        
        img_filename = f"face_{timestamp_suffix}.jpg"
        img_path = os.path.join(faces_dir, img_filename)
        cv2.imwrite(img_path, image)
        
        meta_path = os.path.join(faces_dir, "metadata.json")
        if cipher_suite:
            raw_meta = json.dumps({"nome": nome, "cpf": cpf, "nascimento": nascimento}).encode()
            encrypted_meta = cipher_suite.encrypt(raw_meta)
            with open(meta_path, "wb") as f: f.write(encrypted_meta)
        
        logger.info(f"AUDITORIA: Cadastro de {nome} concluído.")
        return {"status": "success", "name": nome}
    except Exception as e:
        logger.error(f"Erro no cadastro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", dependencies=[Depends(get_api_key)])
async def get_history(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "id": row["id"], "timestamp": row["timestamp"], "image_url": row["image_url"],
                "metadata": {
                    "nome_completo": row["nome_completo"], "cpf": row["cpf"],
                    "data_nascimento": row["data_nascimento"], "ia_prob": row["ia_prob"],
                    "camera_id": row["camera_id"]
                }
            })
        conn.close()
        return results
    except: return []

@router.get("/logs", dependencies=[Depends(get_api_key)])
async def get_logs(lines: int = 100):
    log_path = "logs/app.log"
    if not os.path.exists(log_path):
        return PlainTextResponse("Arquivo de log não encontrado.", status_code=404)
    
    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            return PlainTextResponse("".join(last_lines))
    except Exception as e:
        return PlainTextResponse(f"Erro ao ler logs: {e}", status_code=500)

@router.post("/backup", dependencies=[Depends(get_api_key)])
async def create_local_backup(background_tasks: BackgroundTasks):
    timestamp = int(time.time())
    backup_zip = f"vigia_backup_{timestamp}.zip"
    try:
        with zipfile.ZipFile(backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in ["./database", "./assets"]:
                if os.path.exists(folder):
                    for root, _, files in os.walk(folder):
                        for file in files:
                            full_path = os.path.join(root, file)
                            zipf.write(full_path, os.path.relpath(full_path, "."))
            if os.path.exists("app.log"): zipf.write("app.log", "app.log")

        log_backup(backup_zip, "success")
        background_tasks.add_task(os.remove, backup_zip)
        return FileResponse(path=backup_zip, filename=backup_zip, media_type='application/zip')
    except Exception as e:
          log_backup(backup_zip, f"failed: {str(e)}")
          logger.error(f"Erro na compactação: {e}")
          raise HTTPException(status_code=500, detail="Erro na compactação")

@router.post("/restore_upload", dependencies=[Depends(get_api_key)])
async def restore_from_upload(file: UploadFile = File(...)):
    temp_file_path = f"/tmp/upload_restore_{int(time.time())}.tmp"
    try:
        logger.info(f"AUDITORIA: Recebendo arquivo para restauração direta: {file.filename}")
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extract_path = "."
        if zipfile.is_zipfile(temp_file_path):
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        logger.info("AUDITORIA: Restauração via upload concluída com sucesso.")
        return {"status": "success"}
    except Exception as e:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        logger.error(f"Erro na restauração via upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
