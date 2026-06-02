from typing import Optional, Tuple

import cv2
import numpy as np
from skimage.transform import SimilarityTransform

# Alinhamento ArcFace
reference_alignment: np.ndarray = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041]
    ],
    dtype=np.float32
)


def estimate_norm(landmark: np.ndarray, image_size: int = 112) -> Tuple[np.ndarray, np.ndarray]:
    """Matriz de normalização (landmarks)."""
    if landmark.shape != (5, 2):
        raise ValueError(f"O array de marcos deve ter a forma (5, 2), recebido {landmark.shape}.")
    if image_size % 112 != 0 and image_size % 128 != 0:
        raise ValueError(f"O tamanho da imagem deve ser um múltiplo de 112 ou 128, recebido {image_size}.")

    if image_size % 112 == 0:
        ratio = float(image_size) / 112.0
        diff_x = 0.0
    else:
        ratio = float(image_size) / 128.0
        diff_x = 8.0 * ratio

    # Ajusta o alinhamento de referência com base na proporção e diff_x
    alignment = reference_alignment * ratio
    alignment[:, 0] += diff_x

    # Calcula a matriz de transformação
    transform = SimilarityTransform.from_estimate(landmark, alignment)

    matrix = transform.params[0:2, :]
    inverse_matrix = np.linalg.inv(transform.params)[0:2, :]

    return matrix, inverse_matrix


def face_alignment(image: np.ndarray, landmark: np.ndarray, image_size: int = 112) -> Tuple[np.ndarray, np.ndarray]:
    """Alinha rosto."""
    # Obtém a matriz de transformação
    M, M_inv = estimate_norm(landmark, image_size)

    # Aplica a transformação na imagem de entrada para alinhar o rosto
    warped = cv2.warpAffine(image, M, (image_size, image_size), borderValue=0.0)

    return warped, M_inv


def distance2bbox(
    points: np.ndarray,
    distance: np.ndarray,
    max_shape: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """Decodifica BBox."""
    x1 = points[:, 0] - distance[:, 0]
    y1 = points[:, 1] - distance[:, 1]
    x2 = points[:, 0] + distance[:, 2]
    y2 = points[:, 1] + distance[:, 3]
    if max_shape is not None:
        x1 = np.clip(x1, 0, max_shape[1])
        y1 = np.clip(y1, 0, max_shape[0])
        x2 = np.clip(x2, 0, max_shape[1])
        y2 = np.clip(y2, 0, max_shape[0])
    return np.stack([x1, y1, x2, y2], axis=-1)


def distance2kps(
    points: np.ndarray,
    distance: np.ndarray,
    max_shape: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """Decodifica Keypoints."""
    preds = []
    for i in range(0, distance.shape[1], 2):
        px = points[:, i % 2] + distance[:, i]
        py = points[:, i % 2 + 1] + distance[:, i + 1]
        if max_shape is not None:
            px = np.clip(px, 0, max_shape[1])
            py = np.clip(py, 0, max_shape[0])
        preds.append(px)
        preds.append(py)
    return np.stack(preds, axis=-1)


def compute_similarity(feat1: np.ndarray, feat2: np.ndarray) -> np.float32:
    """Similaridade entre rostos."""
    feat1 = feat1.ravel()
    feat2 = feat2.ravel()
    similarity = np.dot(feat1, feat2) / (np.linalg.norm(feat1) * np.linalg.norm(feat2))
    return similarity


def draw_bbox(
    image: np.ndarray,
    bbox: list[int],
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 3,
    proportion: float = 0.2,
) -> None:
    """Desenha BBox com cantos."""
    x1, y1, x2, y2 = map(int, bbox)
    width = x2 - x1
    height = y2 - y1

    corner_length = int(proportion * min(width, height))

    # Desenha o retângulo
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 1)

    # Canto superior esquerdo
    cv2.line(image, (x1, y1), (x1 + corner_length, y1), color, thickness)
    cv2.line(image, (x1, y1), (x1, y1 + corner_length), color, thickness)

    # Canto superior direito
    cv2.line(image, (x2, y1), (x2 - corner_length, y1), color, thickness)
    cv2.line(image, (x2, y1), (x2, y1 + corner_length), color, thickness)

    # Canto inferior esquerdo
    cv2.line(image, (x1, y2), (x1, y2 - corner_length), color, thickness)
    cv2.line(image, (x1, y2), (x1 + corner_length, y2), color, thickness)

    # Canto inferior direito
    cv2.line(image, (x2, y2), (x2, y2 - corner_length), color, thickness)
    cv2.line(image, (x2, y2), (x2 - corner_length, y2), color, thickness)


def draw_bbox_info(
    frame: np.ndarray,
    bbox: list[int],
    similarity: float,
    name: str,
    color: Tuple[int, int, int],
) -> None:
    """Desenha info da BBox."""
    x1, y1, x2, y2 = map(int, bbox)
    parts = name.split("_")
    lines = []

    # Formata as linhas com base no número de elementos no nome dividido
    if len(parts) >= 1:
        lines.append(f"Nome: {parts[0]} ({similarity:.2f})")
    if len(parts) >= 2:
        lines.append(f"CPF: {parts[1]}")
    if len(parts) >= 3:
        lines.append(f"Nasc: {parts[2]}")

    # Desenha cada linha com espaçamento vertical de 15px
    # Começa a desenhar acima da caixa, garantindo que não saia da tela
    base_y = y1 - 10
    for i, line in enumerate(reversed(lines)):
        text_y = base_y - (i * 15)
        # Impede que o texto saia pelo topo do frame
        text_y = max(text_y, 15)
        
        cv2.putText(
            frame,
            line,
            org=(x1, text_y),
            fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL,
            fontScale=0.8,
            color=color,
            thickness=1,
        )

    # Desenha a caixa delimitadora
    draw_bbox(frame, bbox, color)

    # Desenha a barra de similaridade (limita entre [0, 1] para evitar altura negativa)
    clamped_sim = float(np.clip(similarity, 0.0, 1.0))
    rect_x_start = x2 + 10
    rect_x_end = rect_x_start + 10
    rect_y_end = y2
    rect_height = int(clamped_sim * (y2 - y1))
    rect_y_start = rect_y_end - rect_height

    # Desenha o retângulo preenchido
    cv2.rectangle(frame, (rect_x_start, rect_y_start), (rect_x_end, rect_y_end), color, cv2.FILLED)
