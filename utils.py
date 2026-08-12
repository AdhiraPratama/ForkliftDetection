"""
Utility functions untuk Smart Barrier Gate AI.
"""

from typing import Optional

import cv2
import numpy as np

import config


def safe_crop(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> Optional[np.ndarray]:
    """
    Memotong frame tanpa keluar dari batas gambar.
    """

    if frame is None or frame.size == 0:
        return None

    frame_height, frame_width = frame.shape[:2]

    x1 = max(0, min(int(x1), frame_width - 1))
    y1 = max(0, min(int(y1), frame_height - 1))
    x2 = max(0, min(int(x2), frame_width))
    y2 = max(0, min(int(y2), frame_height))

    if x2 <= x1 or y2 <= y1:
        return None

    return frame[y1:y2, x1:x2].copy()


def detect_red_marker(
    image: np.ndarray,
) -> tuple[bool, float]:
    """
    Mendeteksi warna merah pada area atas bottle.

    Simulasi:
    - Merah terdeteksi = bottle bertutup / forklift bermuatan
    - Merah tidak terdeteksi = bottle tanpa tutup / forklift kosong
    """

    if image is None or image.size == 0:
        return False, 0.0

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    lower_red_1 = np.array(
        [0, 90, 70],
        dtype=np.uint8,
    )
    upper_red_1 = np.array(
        [10, 255, 255],
        dtype=np.uint8,
    )

    lower_red_2 = np.array(
        [170, 90, 70],
        dtype=np.uint8,
    )
    upper_red_2 = np.array(
        [180, 255, 255],
        dtype=np.uint8,
    )

    mask_1 = cv2.inRange(
        hsv,
        lower_red_1,
        upper_red_1,
    )

    mask_2 = cv2.inRange(
        hsv,
        lower_red_2,
        upper_red_2,
    )

    mask = cv2.bitwise_or(
        mask_1,
        mask_2,
    )

    kernel = np.ones(
        (3, 3),
        dtype=np.uint8,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
    )

    red_pixels = cv2.countNonZero(mask)
    total_pixels = image.shape[0] * image.shape[1]

    if total_pixels <= 0:
        return False, 0.0

    red_percent = (
        red_pixels / total_pixels
    ) * 100.0

    detected = (
        red_percent >= config.RED_PERCENT
    )

    return detected, red_percent


def get_box_center(
    bbox: tuple[int, int, int, int],
) -> tuple[int, int]:
    """
    Mengambil titik tengah bounding box.
    """

    x1, y1, x2, y2 = bbox

    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    return center_x, center_y


def get_box_height(
    bbox: tuple[int, int, int, int],
) -> int:
    """
    Mengambil tinggi bounding box.
    """

    _, y1, _, y2 = bbox

    return max(0, y2 - y1)


def get_top_area_bbox(
    bbox: tuple[int, int, int, int],
    ratio: float = 0.35,
) -> tuple[int, int, int, int]:
    """
    Mengambil bagian atas bounding box.

    Dipakai untuk memeriksa area tutup bottle
    atau area muatan forklift.
    """

    x1, y1, x2, y2 = bbox

    box_height = max(0, y2 - y1)
    top_y2 = y1 + int(box_height * ratio)

    return x1, y1, x2, top_y2


def get_zone(
    bbox: tuple[int, int, int, int],
    frame_width: int,
) -> str:
    """
    Menentukan apakah objek berada di zona kiri atau kanan.
    """

    center_x, _ = get_box_center(bbox)

    if center_x < frame_width // 2:
        return "LEFT"

    return "RIGHT"