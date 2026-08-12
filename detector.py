from pathlib import Path
from typing import Any

from ultralytics import YOLO

import config
from distance import estimate_distance, is_within_limit
from utils import (
    detect_red_marker,
    get_box_height,
    get_top_area_bbox,
    get_zone,
    safe_crop,
)


class Detector:
    def __init__(self) -> None:
        self.model = self._load_model()

    @staticmethod
    def _load_model() -> YOLO:
        if Path(config.OPENVINO_MODEL).exists():
            print("Menggunakan model OpenVINO.")

            return YOLO(
                str(config.OPENVINO_MODEL),
                task="detect",
            )

        print("Menggunakan model PyTorch.")

        return YOLO(
            config.YOLO_MODEL,
            task="detect",
        )

    def detect(
        self,
        frame: Any,
        classes: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        if frame is None:
            return []

        result = self.model.predict(
            source=frame,
            imgsz=config.YOLO_IMAGE_SIZE,
            conf=config.YOLO_CONFIDENCE,
            classes=classes,
            verbose=False,
        )[0]

        detections: list[dict[str, Any]] = []

        if result.boxes is None:
            return detections

        frame_width = frame.shape[1]

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist(),
            )

            bbox = (x1, y1, x2, y2)

            object_height_pixels = get_box_height(
                bbox
            )

            distance_meters = estimate_distance(
                object_height_pixels=object_height_pixels,
                real_height_meters=config.REAL_BOTTLE_HEIGHT,
                focal_length_pixels=config.FOCAL_LENGTH,
            )

            within_distance = is_within_limit(
                distance_meters=distance_meters,
                max_distance_meters=config.MAX_DISTANCE,
            )

            top_bbox = get_top_area_bbox(
                bbox,
                ratio=0.35,
            )

            top_crop = safe_crop(
                frame,
                *top_bbox,
            )

            loaded, red_percent = detect_red_marker(
                top_crop
            )

            zone = get_zone(
                bbox=bbox,
                frame_width=frame_width,
            )

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": result.names[class_id],
                    "confidence": confidence,
                    "bbox": bbox,
                    "zone": zone,
                    "distance": distance_meters,
                    "within_distance": within_distance,
                    "loaded": loaded,
                    "red_percent": red_percent,
                }
            )

        return detections