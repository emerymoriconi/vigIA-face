import time
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurações de migração
PC_QDRANT_URL = "http://localhost:6333"
RASP_QDRANT_URL = "http://192.168.0.239:6333"
COLLECTION_NAME = "faces"
BATCH_SIZE = 500

pc_client = QdrantClient(PC_QDRANT_URL)
rasp_client = QdrantClient(RASP_QDRANT_URL)

def migrate():
    """Migra vetores e metadados da coleção 'faces' de um PC para a Raspberry Pi."""
    print(f"Iniciando migração de {PC_QDRANT_URL} para {RASP_QDRANT_URL}...")
    
    # Garante a existência da coleção no destino com otimizações para RPi5
    collections = rasp_client.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        print(f"Criando coleção '{COLLECTION_NAME}' na Raspberry...")
        rasp_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE),
            hnsw_config=models.HnswConfigDiff(on_disk=True) 
        )

    next_page_offset = None
    total_migrated = 0
    start_time = time.time()

    while True:
        # Extração via scrolling
        points, next_page_offset = pc_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=BATCH_SIZE,
            offset=next_page_offset,
            with_vectors=True,
            with_payload=True
        )

        if not points:
            break

        upsert_points = [
            models.PointStruct(id=p.id, vector=p.vector, payload=p.payload) 
            for p in points
        ]

        try:
            rasp_client.upsert(collection_name=COLLECTION_NAME, points=upsert_points, wait=False)
            total_migrated += len(points)
            print(f"Progresso: {total_migrated} pontos enviados...")
        except Exception as e:
            print(f"Erro no lote: {e}")
            time.sleep(2)

        if next_page_offset is None:
            break

    elapsed = time.time() - start_time
    print(f"Migração concluída. Total: {total_migrated} pontos em {elapsed/60:.2f} minutos.")

if __name__ == "__main__":
    migrate()
