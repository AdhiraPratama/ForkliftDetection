"""
MediaPipe Hand Landmarker detector.

Simulation:
1 finger  = forklift without load
2 fingers = forklift with load
"""

import time
from pathlib import Path

import cv2
import mediapipe as mp

import config


class FingerDetector:

    def __init__(self) -> None:

        model_path = Path(config.HAND_MODEL)

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model MediaPipe tidak ditemukan:\n"
                f"{model_path.resolve()}"
            )

        base_options = mp.tasks.BaseOptions(
            model_asset_path=str(model_path)
        )

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=config.HAND_MAX_NUM,
            min_hand_detection_confidence=(
                config.HAND_MIN_DETECTION_CONFIDENCE
            ),
            min_hand_presence_confidence=(
                config.HAND_MIN_PRESENCE_CONFIDENCE
            ),
            min_tracking_confidence=(
                config.HAND_MIN_TRACKING_CONFIDENCE
            ),
        )

        self.landmarker = (
            mp.tasks.vision.HandLandmarker.create_from_options(
                options
            )
        )

        self.start_time = time.perf_counter()

    # ======================================================
    # DETECT
    # ======================================================

    def detect(self, frame):

        if frame is None:
            return []

        height, width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        rgb_frame = rgb_frame.copy()

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        timestamp_ms = int(
            (time.perf_counter() - self.start_time)
            * 1000
        )

        result = self.landmarker.detect_for_video(
            mp_image,
            timestamp_ms,
        )

        detections = []

        if not result.hand_landmarks:
            return detections

        for hand_index, landmarks in enumerate(
            result.hand_landmarks
        ):

            finger_count = self._count_fingers(
                landmarks
            )

            xs = [
                int(point.x * width)
                for point in landmarks
            ]

            ys = [
                int(point.y * height)
                for point in landmarks
            ]

            x1 = max(0, min(xs))
            y1 = max(0, min(ys))
            x2 = min(width - 1, max(xs))
            y2 = min(height - 1, max(ys))

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            if center_x < width // 2:
                zone = "LEFT"
            else:
                zone = "RIGHT"

            state = self._get_vehicle_state(
                finger_count
            )

            handedness = "UNKNOWN"

            if (
                result.handedness
                and hand_index < len(result.handedness)
                and result.handedness[hand_index]
            ):
                handedness = (
                    result.handedness[hand_index][0]
                    .category_name
                )

            detections.append(
                {
                    "finger_count": finger_count,
                    "zone": zone,
                    "vehicle_state": state,
                    "loaded": finger_count == 2,
                    "center": (
                        center_x,
                        center_y,
                    ),
                    "bbox": (
                        x1,
                        y1,
                        x2,
                        y2,
                    ),
                    "handedness": handedness,
                    "landmarks": landmarks,
                }
            )

        return detections

    # ======================================================
    # FINGER COUNT
    # ======================================================

    @staticmethod
    def _count_fingers(landmarks) -> int:
        """
        Untuk simulasi kita hanya membaca:
        index finger
        middle finger

        Thumb, ring, pinky diabaikan.
        """

        count = 0

        # Index
        index_tip = landmarks[8]
        index_pip = landmarks[6]

        if index_tip.y < index_pip.y:
            count += 1

        # Middle
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]

        if middle_tip.y < middle_pip.y:
            count += 1

        return count

    # ======================================================
    # SIMULATION STATE
    # ======================================================

    @staticmethod
    def _get_vehicle_state(
        finger_count: int,
    ) -> str:

        if finger_count == 1:
            return "EMPTY"

        if finger_count == 2:
            return "LOADED"

        return "INVALID"

    # ======================================================
    # DRAW
    # ======================================================

    def draw(
        self,
        frame,
        detections,
    ):

        output = frame.copy()

        height, width = output.shape[:2]

        # Divider IN / OUT
        cv2.line(
            output,
            (width // 2, 0),
            (width // 2, height),
            (255, 0, 255),
            3,
        )

        for detection in detections:

            x1, y1, x2, y2 = (
                detection["bbox"]
            )

            state = detection[
                "vehicle_state"
            ]

            finger_count = detection[
                "finger_count"
            ]

            zone = detection["zone"]

            if state == "EMPTY":
                color = (0, 255, 255)

            elif state == "LOADED":
                color = (0, 255, 0)

            else:
                color = (0, 0, 255)

            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                color,
                3,
            )

            label = (
                f"{zone} | "
                f"{finger_count} JARI | "
                f"{state}"
            )

            cv2.putText(
                output,
                label,
                (
                    x1,
                    max(30, y1 - 12),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA,
            )

            self._draw_landmarks(
                output,
                detection["landmarks"],
            )

        return output

    # ======================================================
    # LANDMARK DRAW
    # ======================================================

    @staticmethod
    def _draw_landmarks(
        frame,
        landmarks,
    ):

        height, width = frame.shape[:2]

        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),

            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),

            (5, 9),
            (9, 10),
            (10, 11),
            (11, 12),

            (9, 13),
            (13, 14),
            (14, 15),
            (15, 16),

            (13, 17),
            (17, 18),
            (18, 19),
            (19, 20),

            (0, 17),
        ]

        points = []

        for landmark in landmarks:

            x = int(
                landmark.x * width
            )

            y = int(
                landmark.y * height
            )

            points.append(
                (x, y)
            )

        for start, end in connections:

            cv2.line(
                frame,
                points[start],
                points[end],
                (255, 255, 255),
                2,
            )

        for point in points:

            cv2.circle(
                frame,
                point,
                4,
                (0, 255, 255),
                -1,
            )

    # ======================================================
    # CLOSE
    # ======================================================

    def close(self):

        self.landmarker.close()