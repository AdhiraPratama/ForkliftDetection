"""
==============================================================
SMART BARRIER GATE AI
MAIN APPLICATION
==============================================================

FLOW:
Camera
    -> Finger Detection
    -> Zone Detection (IN / OUT)
    -> Decision Logic

1 Finger:
    Forklift WITHOUT LOAD
    -> Must remain in zone for 5 seconds
    -> Gate OPEN automatically

2 Fingers:
    Forklift WITH LOAD
    -> Wait for Odoo Validate
    -> Gate OPEN after Validate

Gate command:
    Python -> MQTT -> ESP32 -> Relay -> Barrier Gate
==============================================================
"""

import math
import time
import ctypes

import cv2
import numpy as np

import config

from camera import Camera
from finger_detector import FingerDetector
from odoo_bridge import OdooBridge
from mqtt_gate import MQTTGate


# ============================================================
# CONFIGURATION
# ============================================================

WINDOW_NAME = "AI POWERED SMART BARRIER GATE"

AUTO_OPEN_DELAY = 5.0

# Untuk simulasi finger, jarak fisik belum digunakan.
# Zone ditentukan berdasarkan posisi center tangan.
MAX_DISTANCE = getattr(
    config,
    "MAX_DISTANCE",
    5.0,
)


# ============================================================
# COLORS - BGR
# ============================================================

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

DARK = (35, 35, 35)
GRAY = (125, 125, 125)
LIGHT_GRAY = (170, 170, 170)

GREEN = (80, 175, 65)
GREEN_LIGHT = (110, 220, 95)

RED = (70, 70, 230)
RED_LIGHT = (90, 90, 255)

YELLOW = (50, 225, 255)

PURPLE = (210, 60, 210)


# ============================================================
# DESKTOP SIZE
# ============================================================

def get_desktop_size():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()

        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        return width, height

    except Exception:
        return 1920, 1080


# ============================================================
# INITIAL ZONE STATE
# ============================================================

def create_zone_state():

    return {
        "detected": False,
        "finger_count": 0,
        "loaded": False,

        "entered_at": None,
        "elapsed": 0.0,

        "odoo_validated": False,

        "gate_open": False,

        "command_sent": False,

        "state": "IDLE",

        "status_text": "-",
        "detail_text": "-",
    }


# ============================================================
# RESET DETECTION ONLY
# ============================================================

def reset_detection(state):

    state["detected"] = False
    state["finger_count"] = 0
    state["loaded"] = False


# ============================================================
# RESET COMPLETE CYCLE
# ============================================================

def reset_cycle(state):

    state["detected"] = False
    state["finger_count"] = 0
    state["loaded"] = False

    state["entered_at"] = None
    state["elapsed"] = 0.0

    state["odoo_validated"] = False

    state["gate_open"] = False

    state["command_sent"] = False

    state["state"] = "IDLE"

    state["status_text"] = "-"
    state["detail_text"] = "-"


# ============================================================
# TEXT
# ============================================================

def put_text(
    frame,
    text,
    position,
    scale,
    color,
    thickness=2,
):

    cv2.putText(
        frame,
        str(text),
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


# ============================================================
# TRANSPARENT PANEL
# ============================================================

def transparent_panel(
    frame,
    rectangle,
    alpha=0.78,
):

    x1, y1, x2, y2 = rectangle

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (x1, y1),
        (x2, y2),
        DARK,
        -1,
    )

    cv2.addWeighted(
        overlay,
        alpha,
        frame,
        1.0 - alpha,
        0,
        frame,
    )


# ============================================================
# EXTRACT FINGER COUNT
# ============================================================

def get_finger_count(item):
    """
    Dibuat fleksibel karena struktur output FingerDetector
    bisa berbeda.

    Mendukung key:
    finger_count
    fingers
    count
    """

    if not isinstance(item, dict):
        return 0

    for key in (
        "finger_count",
        "fingers",
        "count",
    ):

        if key in item:

            try:
                return int(item[key])

            except Exception:
                return 0

    return 0


# ============================================================
# EXTRACT HAND CENTER
# ============================================================

def get_hand_center(item):
    """
    Mencoba mendapatkan center tangan.

    Mendukung:
    center = (x, y)

    atau:

    bbox = (x1, y1, x2, y2)
    """

    if not isinstance(item, dict):
        return None

    center = item.get("center")

    if center is not None:

        try:
            return (
                int(center[0]),
                int(center[1]),
            )

        except Exception:
            pass

    bbox = item.get("bbox")

    if bbox is None:
        bbox = item.get("box")

    if bbox is not None:

        try:

            x1, y1, x2, y2 = bbox

            return (
                int((x1 + x2) / 2),
                int((y1 + y2) / 2),
            )

        except Exception:
            pass

    return None


# ============================================================
# EXTRACT BOUNDING BOX
# ============================================================

def get_hand_bbox(item):

    if not isinstance(item, dict):
        return None

    bbox = item.get("bbox")

    if bbox is None:
        bbox = item.get("box")

    if bbox is None:
        return None

    try:

        x1, y1, x2, y2 = bbox

        return (
            int(x1),
            int(y1),
            int(x2),
            int(y2),
        )

    except Exception:

        return None


# ============================================================
# NORMALIZE DETECTOR RESULT
# ============================================================

def normalize_detections(result):
    """
    FingerDetector mungkin mengembalikan:
    dict
    list[dict]
    None

    Semua dinormalisasi menjadi list.
    """

    if result is None:
        return []

    if isinstance(result, dict):
        return [result]

    if isinstance(result, list):
        return result

    return []


# ============================================================
# PROCESS DETECTIONS
# ============================================================

def process_finger_detections(
    detections,
    frame_width,
    left_state,
    right_state,
):

    reset_detection(left_state)
    reset_detection(right_state)

    visual_detections = []

    for item in detections:

        center = get_hand_center(item)

        if center is None:
            continue

        center_x, center_y = center

        finger_count = get_finger_count(item)

        # Kita hanya menggunakan:
        # 1 finger = empty forklift
        # >=2 finger = loaded forklift

        if finger_count <= 0:
            continue

        if center_x < frame_width // 2:

            state = left_state
            zone = "LEFT"

        else:

            state = right_state
            zone = "RIGHT"

        state["detected"] = True

        # Untuk flow simulasi kita batasi:
        # 1 = empty
        # 2+ = loaded

        if finger_count == 1:

            state["finger_count"] = 1
            state["loaded"] = False

        else:

            state["finger_count"] = 2
            state["loaded"] = True

        visual_detections.append(
            {
                "zone": zone,
                "center": center,
                "bbox": get_hand_bbox(item),
                "finger_count": finger_count,
                "loaded": (
                    finger_count >= 2
                ),
            }
        )

    return visual_detections


# ============================================================
# PROCESS ZONE LOGIC
# ============================================================

def process_zone(
    zone_name,
    state,
    odoo_bridge,
):

    now = time.monotonic()

    # --------------------------------------------------------
    # NO FORKLIFT
    # --------------------------------------------------------

    if not state["detected"]:

        # Reset cycle jika forklift sudah meninggalkan zone.

        state["entered_at"] = None
        state["elapsed"] = 0.0

        state["gate_open"] = False
        state["command_sent"] = False

        state["state"] = "IDLE"

        state["status_text"] = "-"
        state["detail_text"] = "-"

        return

    # --------------------------------------------------------
    # GET ODOO STATUS
    # --------------------------------------------------------

    try:

        state["odoo_validated"] = (
            odoo_bridge.get_odoo_validated(
                zone_name
            )
        )

    except Exception:

        state["odoo_validated"] = False

    # ========================================================
    # 1 FINGER = FORKLIFT WITHOUT LOAD
    # ========================================================

    if not state["loaded"]:

        # Odoo tidak diperlukan.

        state["odoo_validated"] = False

        if state["entered_at"] is None:

            state["entered_at"] = now

        state["elapsed"] = (
            now
            - state["entered_at"]
        )

        # ----------------------------------------------------
        # WAITING 5 SECONDS
        # ----------------------------------------------------

        if state["elapsed"] < AUTO_OPEN_DELAY:

            remaining = (
                AUTO_OPEN_DELAY
                - state["elapsed"]
            )

            seconds = max(
                1,
                math.ceil(remaining),
            )

            state["gate_open"] = False

            state["state"] = "WAITING_AUTO"

            state["status_text"] = (
                "FORKLIFT TERDETEKSI "
                "(TIDAK ADA MUATAN)"
            )

            state["detail_text"] = (
                f"TERBUKA DALAM {seconds} DETIK"
            )

        # ----------------------------------------------------
        # AUTO OPEN
        # ----------------------------------------------------

        else:

            state["gate_open"] = True

            state["state"] = "AUTO_OPEN"

            state["status_text"] = (
                "FORKLIFT TERDETEKSI "
                "(TIDAK ADA MUATAN)"
            )

            state["detail_text"] = (
                "AUTO OPEN"
            )

        return

    # ========================================================
    # 2 FINGERS = FORKLIFT WITH LOAD
    # ========================================================

    # Timer tidak digunakan.

    state["entered_at"] = None
    state["elapsed"] = 0.0

    # --------------------------------------------------------
    # ODOO VALIDATED
    # --------------------------------------------------------

    if state["odoo_validated"]:

        state["gate_open"] = True

        state["state"] = "VALIDATED"

        state["status_text"] = (
            "FORKLIFT TERDETEKSI "
            "(ADA MUATAN)"
        )

        state["detail_text"] = (
            "VALIDATE OK"
        )

    # --------------------------------------------------------
    # WAIT ODOO
    # --------------------------------------------------------

    else:

        state["gate_open"] = False

        state["state"] = "WAIT_ODOO"

        state["status_text"] = (
            "FORKLIFT TERDETEKSI "
            "(ADA MUATAN)"
        )

        state["detail_text"] = (
            "LAKUKAN VALIDATE "
            "UNTUK MEMBUKA PORTAL"
        )


# ============================================================
# MQTT OPEN COMMAND
# ============================================================

def send_gate_command(
    mqtt_gate,
    zone,
    state,
):

    # Tidak OPEN
    if not state["gate_open"]:

        state["command_sent"] = False
        return

    # OPEN sudah pernah dikirim untuk cycle ini
    if state["command_sent"]:
        return

    if state["state"] == "AUTO_OPEN":

        source = "AUTO_EMPTY"

    elif state["state"] == "VALIDATED":

        source = "ODOO_VALIDATE"

    else:

        source = "AI"

    try:

        # ----------------------------------------------------
        # Sesuaikan dengan method mqtt_gate.py milik Anda.
        #
        # Prioritas:
        # mqtt_gate.open_gate(...)
        # ----------------------------------------------------

        if hasattr(
            mqtt_gate,
            "open_gate",
        ):

            mqtt_gate.open_gate(
                zone=zone,
                source=source,
            )

        elif hasattr(
            mqtt_gate,
            "publish_open",
        ):

            mqtt_gate.publish_open(
                zone=zone,
                source=source,
            )

        else:

            print(
                "[MQTT WARNING] "
                "Method open_gate() "
                "belum tersedia."
            )

            return

        state["command_sent"] = True

        print(
            f"[GATE] {zone} -> OPEN "
            f"({source})"
        )

    except Exception as error:

        print(
            f"[MQTT ERROR] "
            f"{zone}: {error}"
        )


# ============================================================
# DRAW HAND DETECTION
# ============================================================

def draw_hand_detection(
    canvas,
    item,
    source_width,
    source_height,
    display_rectangle,
):

    dx1, dy1, dx2, dy2 = (
        display_rectangle
    )

    display_width = dx2 - dx1
    display_height = dy2 - dy1

    scale_x = (
        display_width
        / source_width
    )

    scale_y = (
        display_height
        / source_height
    )

    bbox = item["bbox"]

    if bbox is None:
        return

    x1, y1, x2, y2 = bbox

    x1 = (
        dx1
        + int(x1 * scale_x)
    )

    x2 = (
        dx1
        + int(x2 * scale_x)
    )

    y1 = (
        dy1
        + int(y1 * scale_y)
    )

    y2 = (
        dy1
        + int(y2 * scale_y)
    )

    if item["loaded"]:

        color = RED_LIGHT

        label = (
            "FORKLIFT + MUATAN"
        )

    else:

        color = GREEN_LIGHT

        label = (
            "FORKLIFT TANPA MUATAN"
        )

    cv2.rectangle(
        canvas,
        (x1, y1),
        (x2, y2),
        color,
        4,
    )

    put_text(
        canvas,
        label,
        (
            x1,
            max(
                dy1 + 30,
                y1 - 12,
            ),
        ),
        0.65,
        color,
        2,
    )


# ============================================================
# DRAW ZONE STATUS
# ============================================================

def draw_zone_panel(
    canvas,
    rectangle,
    zone_title,
    state,
):

    x1, y1, x2, y2 = rectangle

    transparent_panel(
        canvas,
        rectangle,
        alpha=0.82,
    )

    put_text(
        canvas,
        zone_title,
        (
            x1 + 20,
            y1 + 35,
        ),
        0.85,
        YELLOW,
        2,
    )

    # --------------------------------------------------------
    # STATUS COLOR
    # --------------------------------------------------------

    if state["state"] in (
        "AUTO_OPEN",
        "VALIDATED",
    ):

        status_color = GREEN_LIGHT

    elif state["state"] == "WAIT_ODOO":

        status_color = GREEN_LIGHT

    elif state["state"] == "WAITING_AUTO":

        status_color = YELLOW

    else:

        status_color = RED_LIGHT

    put_text(
        canvas,
        state["status_text"],
        (
            x1 + 20,
            y1 + 70,
        ),
        0.62,
        status_color,
        2,
    )

    detail_color = status_color

    if state["state"] == "WAIT_ODOO":

        detail_color = RED_LIGHT

    put_text(
        canvas,
        state["detail_text"],
        (
            x1 + 20,
            y1 + 102,
        ),
        0.58,
        detail_color,
        2,
    )


# ============================================================
# DRAW BOTTOM GATE PANEL
# ============================================================

def draw_gate_panel(
    canvas,
    rectangle,
    state,
):

    x1, y1, x2, y2 = rectangle

    # --------------------------------------------------------
    # OPEN
    # --------------------------------------------------------

    if state["gate_open"]:

        background = GREEN
        text = "OPEN"
        text_color = BLACK

    # --------------------------------------------------------
    # COUNTDOWN
    # --------------------------------------------------------

    elif state["state"] == "WAITING_AUTO":

        remaining = max(
            1,
            math.ceil(
                AUTO_OPEN_DELAY
                - state["elapsed"]
            ),
        )

        background = YELLOW

        text = (
            f"TERBUKA DALAM "
            f"{remaining} DETIK"
        )

        text_color = BLACK

    # --------------------------------------------------------
    # WAIT ODOO
    # --------------------------------------------------------

    elif state["state"] == "WAIT_ODOO":

        background = RED

        text = "LOCK"

        text_color = BLACK

    # --------------------------------------------------------
    # IDLE
    # --------------------------------------------------------

    else:

        background = LIGHT_GRAY

        text = "ON"

        text_color = BLACK

    cv2.rectangle(
        canvas,
        (x1, y1),
        (x2, y2),
        background,
        -1,
    )

    text_size, _ = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.95,
        3,
    )

    tx = (
        x1
        + (
            (x2 - x1)
            - text_size[0]
        ) // 2
    )

    ty = (
        y1
        + (
            (y2 - y1)
            + text_size[1]
        ) // 2
    )

    put_text(
        canvas,
        text,
        (tx, ty),
        0.95,
        text_color,
        3,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    camera = None
    finger_detector = None
    odoo_bridge = None
    mqtt_gate = None

    left_state = create_zone_state()
    right_state = create_zone_state()

    try:

        # ====================================================
        # INITIALIZATION
        # ====================================================

        print("=" * 65)
        print("SMART BARRIER GATE AI")
        print("=" * 65)

        camera = Camera()

        finger_detector = FingerDetector()

        odoo_bridge = OdooBridge(
            host=config.API_HOST,
            port=config.API_PORT,
        )

        mqtt_gate = MQTTGate()

        # ----------------------------------------------------
        # START SERVICES
        # ----------------------------------------------------

        odoo_bridge.start()

        # MQTTGate bisa memakai start() atau connect()
        if hasattr(
            mqtt_gate,
            "start",
        ):

            mqtt_gate.start()

        elif hasattr(
            mqtt_gate,
            "connect",
        ):

            mqtt_gate.connect()

        camera.start()

        print("Camera           : OK")
        print("Finger Detector  : OK")
        print("Odoo Bridge      : OK")
        print("MQTT             : OK")

        print("=" * 65)

        print(
            "1 JARI = FORKLIFT TANPA MUATAN"
        )

        print(
            "2 JARI = FORKLIFT DENGAN MUATAN"
        )

        print(
            "Q / ESC = EXIT"
        )

        print(
            "F = FULLSCREEN / WINDOWED"
        )

        print("=" * 65)

        # ====================================================
        # WINDOW
        # ====================================================

        desktop_width, desktop_height = (
            get_desktop_size()
        )

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

        # ====================================================
        # FPS
        # ====================================================

        fps = 0.0

        previous_time = (
            time.perf_counter()
        )

        # ====================================================
        # MAIN LOOP
        # ====================================================

        while True:

            frame = camera.read()

            if frame is None:

                print(
                    "Frame kamera tidak tersedia."
                )

                break

            source_height, source_width = (
                frame.shape[:2]
            )

            # ================================================
            # FINGER DETECTION
            # ================================================

            inference_start = (
                time.perf_counter()
            )

            finger_result = (
                finger_detector.detect(
                    frame
                )
            )

            inference_ms = (
                time.perf_counter()
                - inference_start
            ) * 1000.0

            detections = (
                normalize_detections(
                    finger_result
                )
            )

            # ================================================
            # ZONE DETECTION
            # ================================================

            visual_detections = (
                process_finger_detections(
                    detections=detections,
                    frame_width=source_width,
                    left_state=left_state,
                    right_state=right_state,
                )
            )

            # ================================================
            # DECISION LOGIC
            # ================================================

            process_zone(
                zone_name="LEFT",
                state=left_state,
                odoo_bridge=odoo_bridge,
            )

            process_zone(
                zone_name="RIGHT",
                state=right_state,
                odoo_bridge=odoo_bridge,
            )

            # ================================================
            # MQTT COMMAND
            # ================================================

            send_gate_command(
                mqtt_gate=mqtt_gate,
                zone="LEFT",
                state=left_state,
            )

            send_gate_command(
                mqtt_gate=mqtt_gate,
                zone="RIGHT",
                state=right_state,
            )

            # ================================================
            # UPDATE ODOO BRIDGE DECISIONS
            # ================================================

            try:

                odoo_bridge.update_decisions(
                    {
                        "LEFT": {
                            "forklift_detected":
                                left_state[
                                    "detected"
                                ],

                            "within_distance":
                                left_state[
                                    "detected"
                                ],

                            "loaded":
                                left_state[
                                    "loaded"
                                ],

                            "can_validate":
                                (
                                    left_state[
                                        "detected"
                                    ]
                                    and
                                    left_state[
                                        "loaded"
                                    ]
                                ),

                            "odoo_validated":
                                left_state[
                                    "odoo_validated"
                                ],

                            "gate_open":
                                left_state[
                                    "gate_open"
                                ],

                            "status":
                                left_state[
                                    "detail_text"
                                ],
                        },

                        "RIGHT": {
                            "forklift_detected":
                                right_state[
                                    "detected"
                                ],

                            "within_distance":
                                right_state[
                                    "detected"
                                ],

                            "loaded":
                                right_state[
                                    "loaded"
                                ],

                            "can_validate":
                                (
                                    right_state[
                                        "detected"
                                    ]
                                    and
                                    right_state[
                                        "loaded"
                                    ]
                                ),

                            "odoo_validated":
                                right_state[
                                    "odoo_validated"
                                ],

                            "gate_open":
                                right_state[
                                    "gate_open"
                                ],

                            "status":
                                right_state[
                                    "detail_text"
                                ],
                        },
                    }
                )

            except Exception as error:

                # Jangan hentikan AI hanya karena
                # status bridge gagal diperbarui.

                if getattr(
                    config,
                    "DEBUG",
                    False,
                ):

                    print(
                        "[ODOO UPDATE ERROR]",
                        error,
                    )

            # ================================================
            # FPS
            # ================================================

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
                    + current_fps * 0.10
                )

            previous_time = (
                current_time
            )

            # ================================================
            # UI DIMENSIONS
            # ================================================

            width = desktop_width
            height = desktop_height

            header_height = max(
                85,
                int(
                    height * 0.10
                ),
            )

            camera_top = (
                header_height
            )

            camera_bottom = int(
                height * 0.82
            )

            camera_height = (
                camera_bottom
                - camera_top
            )

            bottom_top = (
                camera_bottom + 10
            )

            bottom_bottom = (
                height - 15
            )

            center_x = (
                width // 2
            )

            # ================================================
            # CANVAS
            # ================================================

            canvas = np.zeros(
                (
                    height,
                    width,
                    3,
                ),
                dtype=np.uint8,
            )

            canvas[:] = BLACK

            resized = cv2.resize(
                frame,
                (
                    width,
                    camera_height,
                ),
            )

            canvas[
                camera_top:camera_bottom,
                :
            ] = resized

            # ================================================
            # HEADER
            # ================================================

            cv2.rectangle(
                canvas,
                (0, 0),
                (
                    width,
                    header_height,
                ),
                DARK,
                -1,
            )

            put_text(
                canvas,
                (
                    "AI POWERED "
                    "SMART BARRIER GATE"
                ),
                (
                    40,
                    int(
                        header_height
                        * 0.62
                    ),
                ),
                1.25,
                YELLOW,
                3,
            )

            put_text(
                canvas,
                (
                    f"MAX DISTANCE "
                    f"{MAX_DISTANCE:.1f} M"
                ),
                (
                    width - 330,
                    35,
                ),
                0.62,
                YELLOW,
                2,
            )

            put_text(
                canvas,
                (
                    f"HAND "
                    f"{inference_ms:.0f}MS"
                ),
                (
                    width - 330,
                    63,
                ),
                0.60,
                YELLOW,
                2,
            )

            put_text(
                canvas,
                (
                    f"FPS "
                    f"{fps:.1f}"
                ),
                (
                    width - 330,
                    90,
                ),
                0.60,
                GREEN_LIGHT,
                2,
            )

            # ================================================
            # ZONE BORDER
            # ================================================

            left_border_color = (
                GREEN
                if left_state[
                    "detected"
                ]
                else RED
            )

            right_border_color = (
                GREEN
                if right_state[
                    "detected"
                ]
                else RED
            )

            cv2.rectangle(
                canvas,
                (
                    8,
                    camera_top + 5,
                ),
                (
                    center_x - 8,
                    camera_bottom - 5,
                ),
                left_border_color,
                6,
            )

            cv2.rectangle(
                canvas,
                (
                    center_x + 8,
                    camera_top + 5,
                ),
                (
                    width - 8,
                    camera_bottom - 5,
                ),
                right_border_color,
                6,
            )

            # CENTER LINE

            cv2.line(
                canvas,
                (
                    center_x,
                    camera_top,
                ),
                (
                    center_x,
                    camera_bottom,
                ),
                YELLOW,
                4,
            )

            # ================================================
            # STATUS PANELS
            # ================================================

            left_panel = (
                30,
                camera_top + 20,
                center_x - 30,
                camera_top + 135,
            )

            right_panel = (
                center_x + 30,
                camera_top + 20,
                width - 30,
                camera_top + 135,
            )

            draw_zone_panel(
                canvas,
                left_panel,
                "IN ZONE",
                left_state,
            )

            draw_zone_panel(
                canvas,
                right_panel,
                "OUT ZONE",
                right_state,
            )

            # ================================================
            # HAND BOUNDING BOX
            # ================================================

            display_rect = (
                0,
                camera_top,
                width,
                camera_bottom,
            )

            for item in visual_detections:

                draw_hand_detection(
                    canvas,
                    item,
                    source_width,
                    source_height,
                    display_rect,
                )

            # ================================================
            # BOTTOM STATUS
            # ================================================

            left_bottom = (
                15,
                bottom_top,
                center_x - 8,
                bottom_bottom,
            )

            right_bottom = (
                center_x + 8,
                bottom_top,
                width - 15,
                bottom_bottom,
            )

            draw_gate_panel(
                canvas,
                left_bottom,
                left_state,
            )

            draw_gate_panel(
                canvas,
                right_bottom,
                right_state,
            )

            # ================================================
            # SHOW
            # ================================================

            cv2.imshow(
                WINDOW_NAME,
                canvas,
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

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except KeyboardInterrupt:

        print(
            "Program dihentikan oleh pengguna."
        )

    except Exception as error:

        print(
            f"ERROR: "
            f"{type(error).__name__}: "
            f"{error}"
        )

        raise

    # ========================================================
    # CLEANUP
    # ========================================================

    finally:

        if camera is not None:

            try:
                camera.release()

            except Exception:
                pass

        if finger_detector is not None:

            if hasattr(
                finger_detector,
                "close",
            ):

                try:
                    finger_detector.close()

                except Exception:
                    pass

        if mqtt_gate is not None:

            for method_name in (
                "stop",
                "disconnect",
                "close",
            ):

                if hasattr(
                    mqtt_gate,
                    method_name,
                ):

                    try:

                        getattr(
                            mqtt_gate,
                            method_name,
                        )()

                    except Exception:
                        pass

                    break

        cv2.destroyAllWindows()

        print(
            "Program ditutup."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()