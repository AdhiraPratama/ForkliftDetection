import time
from pathlib import Path

import cv2
from ultralytics import YOLO

from camera import Camera


# ==========================================================
# CONFIG
# ==========================================================

MODEL_PT = Path("models/forklift_load_best.pt")

MODEL_OPENVINO = Path(
    "models/forklift_load_openvino_model"
)

CONFIDENCE = 0.45

# 640 lebih akurat untuk CCTV jauh.
# Kalau FPS terlalu rendah, turunkan ke 512 / 416.
IMAGE_SIZE = 640

WINDOW_NAME = "SMART GATE - FORKLIFT LOAD DETECTION"


# ==========================================================
# COLOR BGR
# ==========================================================

GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (0, 255, 255)
BLACK = (0, 0, 0)


# ==========================================================
# LOAD MODEL
# ==========================================================

def load_model():

    if MODEL_OPENVINO.exists():

        print(
            "Menggunakan OpenVINO model."
        )

        return YOLO(
            str(MODEL_OPENVINO),
            task="detect",
        )

    if MODEL_PT.exists():

        print(
            "Menggunakan PyTorch model."
        )

        return YOLO(
            str(MODEL_PT),
            task="detect",
        )

    raise FileNotFoundError(
        "\nModel forklift belum ditemukan.\n"
        f"PT       : {MODEL_PT.resolve()}\n"
        f"OpenVINO : {MODEL_OPENVINO.resolve()}\n"
    )


# ==========================================================
# DRAW LABEL
# ==========================================================

def draw_label(
    frame,
    text,
    x,
    y,
    color,
):

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.65
    thickness = 2

    (tw, th), _ = cv2.getTextSize(
        text,
        font,
        scale,
        thickness,
    )

    y = max(
        y,
        th + 12,
    )

    cv2.rectangle(
        frame,
        (
            x,
            y - th - 10,
        ),
        (
            x + tw + 12,
            y + 5,
        ),
        BLACK,
        -1,
    )

    cv2.putText(
        frame,
        text,
        (
            x + 5,
            y - 4,
        ),
        font,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    camera = Camera()

    model = load_model()

    print("=" * 65)
    print("FORKLIFT LOAD DETECTION")
    print("=" * 65)

    print(
        "Expected classes:"
    )

    print(
        "0 = forklift_empty"
    )

    print(
        "1 = forklift_loaded"
    )

    print("=" * 65)

    camera.start()

    # ======================================================
    # FULLSCREEN
    # ======================================================

    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL,
    )

    cv2.setWindowProperty(
        WINDOW_NAME,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN,
    )

    fullscreen = True

    # ======================================================
    # FPS
    # ======================================================

    previous_time = (
        time.perf_counter()
    )

    fps = 0.0

    try:

        while True:

            frame = camera.read()

            if frame is None:
                continue

            # ==================================================
            # AI
            # ==================================================

            ai_start = (
                time.perf_counter()
            )

            result = model.predict(
                source=frame,
                conf=CONFIDENCE,
                imgsz=IMAGE_SIZE,
                verbose=False,
            )[0]

            inference_ms = (
                time.perf_counter()
                - ai_start
            ) * 1000.0

            empty_count = 0
            loaded_count = 0

            # ==================================================
            # DETECTIONS
            # ==================================================

            if (
                result.boxes
                is not None
            ):

                for box in result.boxes:

                    class_id = int(
                        box.cls[0]
                    )

                    confidence = float(
                        box.conf[0]
                    )

                    class_name = str(
                        result.names[
                            class_id
                        ]
                    ).lower()

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[
                            0
                        ].tolist(),
                    )

                    # ==========================================
                    # EMPTY
                    # ==========================================

                    if (
                        class_name
                        == "forklift_empty"
                    ):

                        empty_count += 1

                        color = GREEN

                        label = (
                            f"FORKLIFT EMPTY "
                            f"{confidence:.2f}"
                        )

                    # ==========================================
                    # LOADED
                    # ==========================================

                    elif (
                        class_name
                        == "forklift_loaded"
                    ):

                        loaded_count += 1

                        color = RED

                        label = (
                            f"FORKLIFT LOADED "
                            f"{confidence:.2f}"
                        )

                    else:

                        continue

                    # ==========================================
                    # BOX
                    # ==========================================

                    cv2.rectangle(
                        frame,
                        (
                            x1,
                            y1,
                        ),
                        (
                            x2,
                            y2,
                        ),
                        color,
                        4,
                    )

                    draw_label(
                        frame,
                        label,
                        x1,
                        y1,
                        color,
                    )

            # ==================================================
            # FPS
            # ==================================================

            current_time = (
                time.perf_counter()
            )

            elapsed = (
                current_time
                - previous_time
            )

            if elapsed > 0:

                current_fps = (
                    1.0 / elapsed
                )

                fps = (
                    fps * 0.90
                    + current_fps
                    * 0.10
                )

            previous_time = (
                current_time
            )

            # ==================================================
            # HEADER
            # ==================================================

            height, width = (
                frame.shape[:2]
            )

            overlay = frame.copy()

            cv2.rectangle(
                overlay,
                (
                    0,
                    0,
                ),
                (
                    width,
                    100,
                ),
                BLACK,
                -1,
            )

            cv2.addWeighted(
                overlay,
                0.72,
                frame,
                0.28,
                0,
                frame,
            )

            cv2.putText(
                frame,
                (
                    f"EMPTY: "
                    f"{empty_count}"
                ),
                (
                    20,
                    38,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                GREEN,
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                (
                    f"LOADED: "
                    f"{loaded_count}"
                ),
                (
                    20,
                    78,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                RED,
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                frame,
                (
                    f"AI "
                    f"{inference_ms:.0f}ms"
                    f" | FPS "
                    f"{fps:.1f}"
                ),
                (
                    width - 300,
                    38,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.70,
                WHITE,
                2,
                cv2.LINE_AA,
            )

            # ==================================================
            # STATUS
            # ==================================================

            if loaded_count > 0:

                status = (
                    "FORKLIFT DENGAN MUATAN"
                )

                status_color = RED

            elif empty_count > 0:

                status = (
                    "FORKLIFT TANPA MUATAN"
                )

                status_color = GREEN

            else:

                status = (
                    "TIDAK ADA FORKLIFT"
                )

                status_color = YELLOW

            cv2.putText(
                frame,
                status,
                (
                    width - 420,
                    78,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.70,
                status_color,
                2,
                cv2.LINE_AA,
            )

            # ==================================================
            # SHOW
            # ==================================================

            cv2.imshow(
                WINDOW_NAME,
                frame,
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key in (
                ord("q"),
                27,
            ):
                break

            if key == ord("f"):

                fullscreen = (
                    not fullscreen
                )

                cv2.setWindowProperty(
                    WINDOW_NAME,
                    cv2.WND_PROP_FULLSCREEN,
                    (
                        cv2.WINDOW_FULLSCREEN
                        if fullscreen
                        else
                        cv2.WINDOW_NORMAL
                    ),
                )

    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()