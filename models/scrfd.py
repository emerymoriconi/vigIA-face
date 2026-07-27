import logging
from typing import Tuple

import cv2
import numpy as np
import onnxruntime

from src.utils.helpers import distance2bbox, distance2kps

__all__ = ["SCRFD"]

logger = logging.getLogger(__name__)


class SCRFD:
    """Implementação do detector facial SCRFD via ONNX."""

    def __init__(
        self,
        model_path: str,
        input_size: Tuple[int, int] = (640, 640),
        conf_thres: float = 0.5,
        iou_thres: float = 0.4,
    ) -> None:
        """Inicializa parâmetros do SCRFD e carrega o modelo ONNX."""
        self.input_size = input_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

        self.fmc = 3
        self._feat_stride_fpn = [8, 16, 32]
        self._num_anchors = 2
        self.use_kps = True
        self.mean = 127.5
        self.std = 128.0
        self.center_cache = {}

        self._initialize_model(model_path)

    def _initialize_model(self, model_path: str) -> None:
        """Configura a sessão de inferência ONNX."""
        try:
            self.session = onnxruntime.InferenceSession(
                model_path,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
            self.output_names = [x.name for x in self.session.get_outputs()]
            self.input_names = [x.name for x in self.session.get_inputs()]
            logger.info(f"SCRFD carregado: {model_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar SCRFD {model_path}: {e}")
            raise

    def forward(
        self, image: np.ndarray, threshold: float
    ) -> Tuple[list[np.ndarray], list[np.ndarray], list[np.ndarray]]:
        """Executa a inferência e decodifica as saídas (scores, bboxes, kpss)."""
        scores_list = []
        bboxes_list = []
        kpss_list = []
        input_size = tuple(image.shape[0:2][::-1])

        blob = cv2.dnn.blobFromImage(
            image, 1.0 / self.std, input_size,
            (self.mean, self.mean, self.mean), swapRB=True
        )
        outputs = self.session.run(self.output_names, {self.input_names[0]: blob})

        input_height, input_width = blob.shape[2], blob.shape[3]
        fmc = self.fmc

        for idx, stride in enumerate(self._feat_stride_fpn):
            scores = outputs[idx]
            bbox_preds = outputs[idx + fmc] * stride
            if self.use_kps:
                kps_preds = outputs[idx + fmc * 2] * stride

            height, width = input_height // stride, input_width // stride
            key = (height, width, stride)
            
            if key in self.center_cache:
                anchor_centers = self.center_cache[key]
            else:
                anchor_centers = np.stack(np.mgrid[:height, :width][::-1], axis=-1).astype(np.float32)
                anchor_centers = (anchor_centers * stride).reshape((-1, 2))
                if self._num_anchors > 1:
                    anchor_centers = np.stack([anchor_centers] * self._num_anchors, axis=1).reshape((-1, 2))
                if len(self.center_cache) < 100:
                    self.center_cache[key] = anchor_centers

            pos_inds = np.where(scores >= threshold)[0]
            bboxes = distance2bbox(anchor_centers, bbox_preds)
            scores_list.append(scores[pos_inds])
            bboxes_list.append(bboxes[pos_inds])
            
            if self.use_kps:
                kpss = distance2kps(anchor_centers, kps_preds).reshape((-1, 5, 2))
                kpss_list.append(kpss[pos_inds])
                
        return scores_list, bboxes_list, kpss_list

    def detect(
        self, image: np.ndarray, max_num: int = 0, metric: str = "max"
    ) -> Tuple[np.ndarray, np.ndarray | None]:
        """Pipeline completo: redimensionamento, inferência, NMS e filtragem por área/posição."""
        width, height = self.input_size
        im_ratio = float(image.shape[0]) / image.shape[1]
        model_ratio = height / width
        
        if im_ratio > model_ratio:
            new_height = height
            new_width = int(new_height / im_ratio)
        else:
            new_width = width
            new_height = int(new_width * im_ratio)

        det_scale = float(new_height) / image.shape[0]
        resized_image = cv2.resize(image, (new_width, new_height))

        det_image = np.zeros((height, width, 3), dtype=np.uint8)
        det_image[:new_height, :new_width, :] = resized_image

        scores_list, bboxes_list, kpss_list = self.forward(det_image, self.conf_thres)

        if scores_list is None or len(scores_list) == 0:
            return np.empty((0, 5)), None

        scores = np.vstack(scores_list)
        order = scores.ravel().argsort()[::-1]
        bboxes = np.vstack(bboxes_list) / det_scale

        pre_det = np.hstack((bboxes, scores)).astype(np.float32, copy=False)
        pre_det = pre_det[order, :]
        keep = self.nms(pre_det, iou_thres=self.iou_thres)
        det = pre_det[keep, :]
        
        kpss = None
        if self.use_kps and kpss_list is not None and len(kpss_list) > 0:
            kpss = np.vstack(kpss_list) / det_scale
            kpss = kpss[order, :, :][keep, :, :]

        if 0 < max_num < det.shape[0]:
            area = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
            img_c = image.shape[0] // 2, image.shape[1] // 2
            offsets = np.vstack([(det[:, 0]+det[:, 2])/2 - img_c[1], (det[:, 1]+det[:, 3])/2 - img_c[0]])
            off_dist = np.sum(np.power(offsets, 2.0), 0)
            values = area if metric == "max" else (area - off_dist * 2.0)
            bindex = np.argsort(values)[::-1][:max_num]
            det = det[bindex, :]
            if kpss is not None: kpss = kpss[bindex, :]
            
        return det, kpss

    def nms(self, dets: np.ndarray, iou_thres: float) -> list[int]:
        """Supressão não máxima (NMS) para eliminar detecções sobrepostas."""
        x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)

            indices = np.where(ovr <= iou_thres)[0]
            order = order[indices + 1]

        return keep
