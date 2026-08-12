"""
SMART BARRIER GATE AI
Configuration File

Seluruh konfigurasi aplikasi berada di file ini.
"""

from pathlib import Path


# ==========================================================
# PROJECT
# ==========================================================

PROJECT_NAME = "Smart Barrier Gate AI"
VERSION = "1.0.0"


# ==========================================================
# CAMERA
# ==========================================================

# 0 = kamera laptop
# 1 = webcam Logitech
# 2 = kamera lainnya

CAMERA_INDEX = 1
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
CAMERA_BUFFERSIZE = 1


# ==========================================================
# WINDOW
# ==========================================================

WINDOW_NAME = "Smart Barrier Gate"
FULLSCREEN = True


# ==========================================================
# MODEL
# ==========================================================

OPENVINO_MODEL = Path("yolo11n_openvino_model")
YOLO_MODEL = "yolo11n.pt"

YOLO_IMAGE_SIZE = 320
YOLO_CONFIDENCE = 0.15


# ==========================================================
# COCO CLASS
# ==========================================================

CLASS_PERSON = 0
CLASS_BOTTLE = 39


# ==========================================================
# DISTANCE
# ==========================================================

MAX_DISTANCE = 5.0
REAL_BOTTLE_HEIGHT = 0.25
FOCAL_LENGTH = 800.0


# ==========================================================
# RED MARKER
# ==========================================================

RED_PERCENT = 2.0


# ==========================================================
# UI
# ==========================================================

HEADER_HEIGHT_PERCENT = 0.075
CAMERA_AREA_PERCENT = 0.78

BUTTON_MARGIN = 30
CENTER_GAP = 18


# ==========================================================
# COLORS (BGR)
# ==========================================================

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
DARK = (35, 35, 35)

GREEN = (0, 190, 0)
GREEN_LIGHT = (90, 255, 90)

RED = (0, 0, 255)
RED_LIGHT = (80, 80, 255)

YELLOW = (0, 255, 255)
BLUE = (255, 170, 0)
PURPLE = (255, 0, 255)


# ==========================================================
# TEXT
# ==========================================================

FONT = 0
FONT_TITLE = 1.0
FONT_NORMAL = 0.70
FONT_SMALL = 0.55


# ==========================================================
# PERFORMANCE
# ==========================================================

ENABLE_FPS = True


# ==========================================================
# DEBUG
# ==========================================================

DEBUG = False
# ==========================================================
# ODOO BRIDGE API
# ==========================================================

API_HOST = "0.0.0.0"
API_PORT = 5000

# ==========================================================
# MQTT
# ==========================================================

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

MQTT_USERNAME = ""
MQTT_PASSWORD = ""

MQTT_CLIENT_ID = "smart-gate-ai-python-rm-gate-01"
MQTT_GATE_ID = "RM_GATE_01"

MQTT_QOS = 0
MQTT_KEEPALIVE = 60

MQTT_TOPIC_AI = (
    "metindo/smartgate/RM_GATE_01/ai"
)

MQTT_TOPIC_VALIDATE = (
    "metindo/smartgate/RM_GATE_01/validate"
)

MQTT_TOPIC_COMMAND = (
    "metindo/smartgate/RM_GATE_01/command"
)

MQTT_TOPIC_STATUS = (
    "metindo/smartgate/RM_GATE_01/status"
)

MQTT_TOPIC_HEARTBEAT = (
    "metindo/smartgate/RM_GATE_01/heartbeat"
)

MQTT_TOPIC_EMERGENCY = (
    "metindo/smartgate/RM_GATE_01/emergency"
)

MQTT_TOPIC_EVENT = (
    "metindo/smartgate/RM_GATE_01/event"
)

# ==========================================================
# HAND / FINGER SIMULATION
# ==========================================================

# Simulasi:
# 1 jari = forklift tanpa muatan
# 2 jari = forklift dengan muatan

FINGER_EMPTY = 1
FINGER_LOADED = 2

# Berapa lama forklift tanpa muatan harus stabil di zone
AUTO_OPEN_DELAY = 5.0

# Minimum waktu deteksi agar tidak mudah flicker
DETECTION_STABLE_TIME = 0.30

# Jika tangan hilang selama waktu ini, status dianggap hilang
DETECTION_LOST_TIMEOUT = 0.50


# ==========================================================
# ZONE
# ==========================================================

# Kamera dibagi dua:
# LEFT  = IN
# RIGHT = OUT

ZONE_LEFT_NAME = "IN"
ZONE_RIGHT_NAME = "OUT"


# ==========================================================
# DISTANCE
# ==========================================================

MAX_DISTANCE = 5.0


# ==========================================================
# MEDIAPIPE HAND
# ==========================================================

HAND_MAX_NUM = 2

HAND_MIN_DETECTION_CONFIDENCE = 0.60
HAND_MIN_TRACKING_CONFIDENCE = 0.60

# ==========================================================
# HAND LANDMARKER
# ==========================================================

HAND_MODEL = "models/hand_landmarker.task"

HAND_MAX_NUM = 1

HAND_MIN_DETECTION_CONFIDENCE = 0.60
HAND_MIN_PRESENCE_CONFIDENCE = 0.60
HAND_MIN_TRACKING_CONFIDENCE = 0.60

FINGER_EMPTY = 1
FINGER_LOADED = 2

AUTO_OPEN_DELAY = 5.0

# ==========================================================
# CAMERA SOURCE
# ==========================================================

# Pilihan:
# "USB"  = Logitech / webcam
# "RTSP" = CCTV / NVR Hikvision

CAMERA_SOURCE = "RTSP"


# ==========================================================
# USB CAMERA
# ==========================================================

# Dipakai hanya jika CAMERA_SOURCE = "USB"

CAMERA_INDEX = 0

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

CAMERA_BUFFERSIZE = 1


# ==========================================================
# HIKVISION / NVR RTSP
# ==========================================================

RTSP_IP = "192.168.6.11"

RTSP_PORT = 554

RTSP_USERNAME = "admin"

# Ganti dengan password NVR/CCTV
RTSP_PASSWORD = "mes@1989"


# ==========================================================
# CHANNEL
# ==========================================================

# Screenshot menunjukkan Cam014.
RTSP_CHANNEL = 14

# 1 = Main Stream
# 2 = Sub Stream
#
# Untuk AI disarankan mulai dari Sub Stream karena lebih ringan.

RTSP_STREAM = 2


# ==========================================================
# RTSP SETTINGS
# ==========================================================

RTSP_RECONNECT_DELAY = 2.0

RTSP_BUFFER_SIZE = 1