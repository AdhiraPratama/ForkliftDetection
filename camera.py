"""
============================================================
SMART BARRIER GATE
Camera Manager
============================================================

Support:
- USB Webcam
- Hikvision / NVR RTSP

main.py cukup memanggil:

camera = Camera()
camera.start()
frame = camera.read()
"""

import time

import cv2

import config


class Camera:

    def __init__(self):

        self.cap = None

        self.source_type = (
            config.CAMERA_SOURCE
            .strip()
            .upper()
        )

        self.rtsp_url = None

        self.last_reconnect_time = 0.0

    # ======================================================
    # START
    # ======================================================

    def start(self):

        print("=" * 60)

        print(
            f"Camera source : "
            f"{self.source_type}"
        )

        if self.source_type == "USB":

            self._start_usb()

        elif self.source_type == "RTSP":

            self._start_rtsp()

        else:

            raise ValueError(
                "CAMERA_SOURCE harus "
                "'USB' atau 'RTSP'"
            )

        print("=" * 60)

    # ======================================================
    # USB CAMERA
    # ======================================================

    def _start_usb(self):

        print(
            f"Membuka USB Camera "
            f"index {config.CAMERA_INDEX}..."
        )

        self.cap = cv2.VideoCapture(
            config.CAMERA_INDEX,
            cv2.CAP_DSHOW,
        )

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Tidak dapat membuka "
                f"USB camera index "
                f"{config.CAMERA_INDEX}"
            )

        # MJPG biasanya lebih ringan untuk Logitech

        self.cap.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(
                *"MJPG"
            ),
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            config.CAMERA_WIDTH,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            config.CAMERA_HEIGHT,
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            config.CAMERA_FPS,
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            config.CAMERA_BUFFERSIZE,
        )

        print(
            "USB Camera berhasil dibuka."
        )

    # ======================================================
    # BUILD RTSP URL
    # ======================================================

    @staticmethod
    def _build_rtsp_url():

        channel = (
            config.RTSP_CHANNEL * 100
            + config.RTSP_STREAM
        )

        return (
            f"rtsp://"
            f"{config.RTSP_USERNAME}:"
            f"{config.RTSP_PASSWORD}@"
            f"{config.RTSP_IP}:"
            f"{config.RTSP_PORT}/"
            f"Streaming/channels/"
            f"{channel}"
        )

    # ======================================================
    # RTSP CAMERA
    # ======================================================

    def _start_rtsp(self):

        self.rtsp_url = (
            self._build_rtsp_url()
        )

        # Jangan print password ke terminal.

        channel = (
            config.RTSP_CHANNEL * 100
            + config.RTSP_STREAM
        )

        print(
            f"Membuka Hikvision/NVR..."
        )

        print(
            f"IP      : "
            f"{config.RTSP_IP}"
        )

        print(
            f"Channel : "
            f"{config.RTSP_CHANNEL}"
        )

        print(
            f"Stream  : "
            f"{config.RTSP_STREAM}"
        )

        print(
            f"RTSP ID : {channel}"
        )

        self.cap = cv2.VideoCapture(
            self.rtsp_url,
            cv2.CAP_FFMPEG,
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            config.RTSP_BUFFER_SIZE,
        )

        if not self.cap.isOpened():

            self.cap.release()

            self.cap = None

            raise RuntimeError(
                "Tidak dapat membuka "
                "RTSP Hikvision.\n"
                "Periksa IP, username, "
                "password, port dan channel."
            )

        # Test membaca satu frame.

        success, frame = (
            self.cap.read()
        )

        if (
            not success
            or frame is None
        ):

            self.cap.release()

            self.cap = None

            raise RuntimeError(
                "RTSP terkoneksi tetapi "
                "frame tidak dapat dibaca."
            )

        height, width = (
            frame.shape[:2]
        )

        print(
            "RTSP berhasil dibuka."
        )

        print(
            f"Stream resolution : "
            f"{width}x{height}"
        )

    # ======================================================
    # READ
    # ======================================================

    def read(self):

        if self.cap is None:

            return None

        success, frame = (
            self.cap.read()
        )

        if (
            success
            and frame is not None
        ):

            return frame

        # USB:
        # kalau gagal cukup return None

        if self.source_type == "USB":

            return None

        # RTSP:
        # coba reconnect

        return self._reconnect_rtsp()

    # ======================================================
    # RTSP RECONNECT
    # ======================================================

    def _reconnect_rtsp(self):

        now = time.time()

        if (
            now
            - self.last_reconnect_time
            <
            config.RTSP_RECONNECT_DELAY
        ):

            return None

        self.last_reconnect_time = now

        print(
            "RTSP terputus. "
            "Mencoba reconnect..."
        )

        if self.cap is not None:

            self.cap.release()

        self.cap = cv2.VideoCapture(
            self.rtsp_url,
            cv2.CAP_FFMPEG,
        )

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            config.RTSP_BUFFER_SIZE,
        )

        if not self.cap.isOpened():

            print(
                "Reconnect RTSP gagal."
            )

            return None

        success, frame = (
            self.cap.read()
        )

        if (
            success
            and frame is not None
        ):

            print(
                "RTSP reconnect berhasil."
            )

            return frame

        return None

    # ======================================================
    # RELEASE
    # ======================================================

    def release(self):

        if self.cap is not None:

            self.cap.release()

            self.cap = None

        print(
            "Camera ditutup."
        )