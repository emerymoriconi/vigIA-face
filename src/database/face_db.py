import logging
from typing import Tuple, List, Dict
import uuid

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

class FaceDatabase:
    """DB de embeddings (Qdrant SERVER)."""

    def __init__(
        self,
        embedding_size: int = 512,
        collection_name: str = "faces",
        host: str = "localhost",
        port: int = 6333,
        path: str = None # Ignorado, mantido para compatibilidade
    ) -> None:
        """Conexão Qdrant via Docker."""
        self.embedding_size = embedding_size
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.client = None
        self.index = type('obj', (object,), {'ntotal': 0})
        
        self._connect()

    def _connect(self):
        """Conecta ao servidor Qdrant."""
        try:
            logger.info(f"Conectando ao Qdrant SERVER em {self.host}:{self.port}")
            self.client = QdrantClient(host=self.host, port=self.port, timeout=30)
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao Qdrant: {e}")
            return False

    def load(self) -> bool:
        """Garante coleção e inicializa contagem."""
        try:
            if self.client is None and not self._connect():
                return False
            
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Criando nova coleção '{self.collection_name}' OTIMIZADA...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_size,
                        distance=models.Distance.COSINE
                    ),
                    # HNSW para velocidade
                    hnsw_config=models.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000
                    ),
                    # Quantização INT8 (reduz RAM e acelera busca)
                    quantization_config=models.ScalarQuantization(
                        scalar=models.ScalarQuantizationConfig(
                            type=models.ScalarType.INT8,
                            quantile=0.99,
                            always_ram=True
                        )
                    )
                )
            
            self._update_total()
            logger.info(f"Conectado ao Docker. Faces: {self.index.ntotal}")
            return True
        except Exception as e:
            logger.error(f"Falha ao carregar Qdrant no Docker: {e}")
            return False

    def close(self) -> None:
        """Fecha conexão."""
        if self.client:
            self.client = None
            logger.info("Conexão Qdrant encerrada.")

    def add_face(self, embedding: np.ndarray, payload: any) -> None:
        """Adiciona embedding ao Docker. payload pode ser string ou dict."""
        if self.client is None: self.load()
        vec = self._normalise(embedding).tolist()
        
        final_payload = payload if isinstance(payload, dict) else {"name": str(payload)}
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload=final_payload
                )
            ]
        )
        self._update_total()

    def _extract_name(self, payload: Dict) -> str:
        """Extrai metadados do payload de forma robusta para o motor de IA."""
        if not payload: return "Unknown"
        
        # 1. Tenta buscar no objeto 'metadata' (Snapshot Original ou Novo Formato)
        if "metadata" in payload and isinstance(payload["metadata"], dict):
            meta = payload["metadata"]
            nome = meta.get("name") or meta.get("nome")
            cpf = meta.get("cpf") or meta.get("id") or "N/A"
            nasc = meta.get("birthdate") or meta.get("nascimento") or "N/A"
            
            if nome:
                # Retorna no formato pipe esperado pelo engine.py para preservar o CPF
                return f"{cpf}|{nome}|{nasc}"

        # 2. Tenta buscar no campo 'name' direto (Formato Legado ou Fallback)
        name_val = payload.get("name") or payload.get("nome")
        
        if name_val is not None:
            if isinstance(name_val, np.ndarray):
                name_str = str(name_val.flatten()[0]) if name_val.size > 0 else "Unknown"
            else:
                name_str = str(name_val)
            
            # Se for o formato legado com pipes, retorna na íntegra para o engine processar
            # (CPF|NOME|DATA|TS)
            if "|" in name_str:
                return name_str.strip()
                
            return name_str.strip()
        
        # 3. Fallback para person_id
        return payload.get("person_id") or "Unknown"

    def search(self, embedding: np.ndarray, threshold: float = 0.35) -> Tuple[str, float]:
        """Busca Qdrant (query_points)."""
        if self.index.ntotal == 0:
            return "Unknown", 0.0

        if self.client is None: self.load()
        vec = self._normalise(embedding).tolist()
        
        try:
            # ef=256 e rescore=True para máxima acurácia
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=vec,
                limit=1,
                with_payload=True,
                params=models.SearchParams(
                    hnsw_ef=256,
                    quantization=models.QuantizationSearchParams(
                        rescore=True
                    )
                )
            )
            
            if response.points:
                best_hit = response.points[0]
                similarity = float(best_hit.score)
                name = self._extract_name(best_hit.payload)
                
                logger.debug(f"Busca Qdrant: Encontrado '{name}' com score {similarity:.4f}")
                
                if similarity > threshold:
                    return name, similarity
                return "Unknown", similarity
            return "Unknown", 0.0
        except Exception as e:
            logger.error(f"Erro na busca Qdrant Docker (query_points): {e}")
            return "Unknown", 0.0

    def add_faces_batch(self, embeddings: List[np.ndarray], payloads: List[any]) -> None:
        """Inserção em lote. payloads podem ser strings ou dicts."""
        if not embeddings: return
        if self.client is None: self.load()
        
        points = []
        for i, emb in enumerate(embeddings):
            p = payloads[i]
            final_p = p if isinstance(p, dict) else {"name": str(p)}
            
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                vector=self._normalise(emb).tolist(),
                payload=final_p
            ))
        
        self.client.upsert(collection_name=self.collection_name, points=points)
        self._update_total()

    def batch_search(
        self,
        embeddings: List[np.ndarray],
        threshold: float = 0.4,
    ) -> List[Tuple[str, float]]:
        """Busca em lote (query_batch_points)."""
        if not embeddings: return []
        if self.index.ntotal == 0: return [("Unknown", 0.0)] * len(embeddings)
        if self.client is None: self.load()

        try:
            requests = [
                models.QueryRequest(
                    query=self._normalise(emb).tolist(),
                    limit=1,
                    with_payload=True,
                    params=models.SearchParams(
                        hnsw_ef=256,
                        quantization=models.QuantizationSearchParams(
                            rescore=True
                        )
                    )
                ) for emb in embeddings
            ]
            
            batch_responses = self.client.query_batch_points(
                collection_name=self.collection_name,
                requests=requests
            )
            
            results = []
            for response in batch_responses:
                if response.points:
                    best_hit = response.points[0]
                    similarity = float(best_hit.score)
                    if similarity > threshold:
                        results.append((self._extract_name(best_hit.payload), similarity))
                    else:
                        results.append(("Unknown", similarity))
                else:
                    results.append(("Unknown", 0.0))
            return results
            
        except Exception as e:
            logger.error(f"Erro no batch_search Qdrant Docker (query_batch_points): {e}")
            return [("Unknown", 0.0)] * len(embeddings)

    def get_all_people(self) -> List[Dict]:
        """Recupera metadados de pessoas."""
        try:
            if self.client is None: self.load()
            
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=100, 
                with_payload=True,
                with_vectors=False
            )[0]
            
            people_map = {}
            for point in scroll_result:
                payload = point.payload
                
                # Formato 1: Objeto metadata
                if "metadata" in payload and isinstance(payload["metadata"], dict):
                    meta = payload["metadata"]
                    cpf = meta.get("cpf") or meta.get("id")
                    if cpf and cpf not in people_map:
                        people_map[cpf] = {
                            "cpf": cpf,
                            "nome": meta.get("name") or meta.get("nome") or "N/A",
                            "nascimento": meta.get("birthdate") or meta.get("nascimento") or "N/A"
                        }
                
                # Formato 2: String formatada com |
                else:
                    name_payload = payload.get("name") or payload.get("nome", "")
                    
                    # Trata possível ambiguidade se name_payload for um array
                    if isinstance(name_payload, np.ndarray):
                        name_payload = str(name_payload.flatten()[0]) if name_payload.size > 0 else "Unknown"
                    else:
                        name_payload = str(name_payload)

                    if "|" in name_payload:
                        parts = name_payload.split("|")
                        cpf = parts[0]
                        if cpf not in people_map:
                            people_map[cpf] = {
                                "cpf": cpf,
                                "nome": parts[1] if len(parts) > 1 else "N/A",
                                "nascimento": parts[2] if len(parts) > 2 else "N/A"
                            }
                    elif name_payload and "person_id" in payload:
                        cpf = payload["person_id"]
                        if cpf not in people_map:
                            people_map[cpf] = {
                                "cpf": cpf,
                                "nome": name_payload,
                                "nascimento": "N/A"
                            }
            return list(people_map.values())
        except Exception as e:
            logger.error(f"Erro ao recuperar pessoas do Docker: {e}")
            return []

    def count_unique_people(self) -> int:
        """Total de pontos no banco."""
        try:
            if self.client is None: self.load()
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except:
            return 0
        
    def _update_total(self):
        """Atualiza contagem de pontos."""
        try:
            if self.client is None: return
            info = self.client.get_collection(self.collection_name)
            self.index.ntotal = info.points_count
        except:
            pass

    @staticmethod
    def _normalise(vec: np.ndarray) -> np.ndarray:
        """Normalização L2."""
        v = vec.astype(np.float32).ravel()
        norm = np.linalg.norm(v)
        if norm > 0: v /= norm
        return v
