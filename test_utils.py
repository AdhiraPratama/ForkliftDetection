import cv2
import numpy as np

from utils import (
    detect_red_marker,
    get_box_center,
    get_box_height,
    get_top_area_bbox,
    get_zone,
    safe_crop,
)


def main() -> None:
    frame = np.zeros(
        (480, 640, 3),
        dtype=np.uint8,
    )

    # Buat kotak merah untuk simulasi marker.
    cv2.rectangle(
        frame,
        (100, 100),
        (200, 180),
        (0, 0, 255),
        -1,
    )

    bbox = (80, 80, 220, 350)

    crop = safe_crop(
        frame,
        *bbox,
    )

    top_bbox = get_top_area_bbox(
        bbox,
        ratio=0.35,
    )

    top_crop = safe_crop(
        frame,
        *top_bbox,
    )

    marker_detected, red_percent = (
        detect_red_marker(top_crop)
    )

    print(
        "Center:",
        get_box_center(bbox),
    )

    print(
        "Height:",
        get_box_height(bbox),
    )

    print(
        "Zone:",
        get_zone(
            bbox,
            frame_width=640,
        ),
    )

    print(
        "Red marker:",
        marker_detected,
    )

    print(
        f"Red percent: {red_percent:.2f}%",
    )

    if crop is not None:
        cv2.rectangle(
            frame,
            (bbox[0], bbox[1]),
            (bbox[2], bbox[3]),
            (0, 255, 0),
            2,
        )

    cv2.imshow(
        "Utils Test",
        frame,
    )

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()