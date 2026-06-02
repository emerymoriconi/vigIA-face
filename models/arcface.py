from logging import getLogger
from typing import List

import cv2
import numpy as np
from onnxruntime import InferenceSession

from src.utils.helpers import face_alignment

__all__ = ["ArcFace"]

logger = getLogger(__name__)


class ArcFace:
    """Implementação do ArcFace para extração de embeddings faciais via ONNX."""

    def __init__(self, model_path: str) -> None:
        """Inicializa a sessão ONNX e configura parâmetros de entrada/saída."""
        self.model_path = model_path
        self.input_size = (112, 112)
        self.normalization_mean = 127.5
        self.normalization_scale = 127.5

        logger.info(f"Carregando ArcFace: {self.model_path}")

        try:
            self.session = InferenceSession(
                self.model_path,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )

            input_config = self.session.get_inputs()[0]
            self.input_name = input_config.name
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.embedding_size = self.session.get_outputs()[0].shape[1]

            logger.info(f"ArcFace carregado. Embedding size: {self.embedding_size}")

        except Exception as e:
            logger.error(f"Erro ao carregar ArcFace de {self.model_path}: {e}")
            raise RuntimeError(f"Falha na inicialização do modelo: {self.model_path}") from e

    def preprocess(self, face_image: np.ndarray) -> np.ndarray:
        """Redimensiona e normaliza a face para o formato NCHW exigido pelo modelo."""
        resized_face = cv2.resize(face_image, self.input_size)

        if isinstance(self.normalization_scale, (list, tuple)):
            rgb_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2RGB).astype(np.float32)
            mean_array = np.array(self.normalization_mean, dtype=np.float32)
            scale_array = np.array(self.normalization_scale, dtype=np.float32)
            normalized_face = (rgb_face - mean_array) / scale_array
            transposed_face = np.transpose(normalized_face, (2, 0, 1))
            face_blob = np.expand_dims(transposed_face, axis=0)
        else:
            face_blob = cv2.dnn.blobFromImage(
                resized_face,
                scalefactor=1.0 / self.normalization_scale,
                size=self.input_size,
                mean=(self.normalization_mean,)*3,
                swapRB=True
            )
        return face_blob

    def get_embedding(
        self,
        image: np.ndarray,
        landmarks: np.ndarray,
        normalized: bool = False
    ) -> np.ndarray:
        """Alinha a face e extrai um único vetor de embedding."""
        if image is None or landmarks is None:
            raise ValueError("Parâmetros inválidos")

        embeddings = self.get_embeddings_batch(image, [landmarks], normalized)
        return embeddings[0] if embeddings else None

    def get_embeddings_batch(
        self,
        image: np.ndarray,
        landmarks_list: List[np.ndarray],
        normalized: bool = False
    ) -> List[np.ndarray]:
        """Extrai embeddings em lote para múltiplos rostos em uma imagem."""
        if image is None or landmarks_list is None or len(landmarks_list) == 0:
            return []

        try:
            aligned_faces_blobs = []
            for landmarks in landmarks_list:
                aligned_face, _ = face_alignment(image, landmarks)
                face_blob = self.preprocess(aligned_face)
                aligned_faces_blobs.append(face_blob)

            batch_blob = np.vstack(aligned_faces_blobs)
            embeddings = self.session.run(self.output_names, {self.input_name: batch_blob})[0]

            if normalized:
                norm = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / norm

            return [embeddings[i].flatten() for i in range(len(embeddings))]

        except Exception as e:
            logger.error(f"Erro no batch_search ArcFace: {e}")
            return []
