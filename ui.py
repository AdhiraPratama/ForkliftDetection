"""
Tampilan Smart Barrier Gate AI menggunakan OpenCV.
"""

import ctypes
import time
from typing import Any

import cv2
import numpy as np

import config


class SmartGateUI:
    def __init__(self) -> None:
        self.window_name = config.WINDOW_NAME
        self.desktop_width, self.desktop_height = self._get_desktop_size()

        self.left_button: tuple[int, int, int, int] | None = None
        self.right_button: tuple[int, int, int, int] | None = None

        self.last_message = "Sistem siap"
        self.last_message_time = 0.0

        self.fullscreen = config.FULLSCREEN

        cv2.namedWindow(
            self.window_name,
            cv2.WINDOW_NORMAL,
        )

        if self.fullscreen:
            cv2.setWindowProperty(
                self.window_name,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN,
            )

        cv2.setMouseCallback(
            self.window_name,
            self._mouse_callback,
        )

    @staticmethod
    def _get_desktop_size() -> tuple[int, int]:
        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            return (
                user32.GetSystemMetrics(0),
                user32.GetSystemMetrics(1),
            )

        except Exception:
            return 1920, 1080

    @staticmethod
    def _draw_transparent_panel(
        frame: np.ndarray,
        rectangle: tuple[int, int, int, int],
        color: tuple[int, int, int] = (15, 15, 15),
        alpha: float = 0.78,
    ) -> None:
        overlay = frame.copy()
        x1, y1, x2, y2 = rectangle

        cv2.rectangle(
            overlay,
            (x1, y1),
            (x2, y2),
            color,
            -1,
        )

        cv2.addWeighted(
            overlay,
            alpha,
            frame,
            1 - alpha,
            0,
            frame,
        )

    @staticmethod
    def _draw_centered_text(
        frame: np.ndarray,
        text: str,
        rectangle: tuple[int, int, int, int],
        font_scale: float,
        color: tuple[int, int, int],
        thickness: int,
    ) -> None:
        x1, y1, x2, y2 = rectangle

        text_size, _ = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            thickness,
        )

        text_width, text_height = text_size

        text_x = x1 + ((x2 - x1) - text_width) // 2
        text_y = y1 + ((y2 - y1) + text_height) // 2

        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    def _draw_button(
        self,
        frame: np.ndarray,
        rectangle: tuple[int, int, int, int],
        title: str,
        enabled: bool,
    ) -> None:
        x1, y1, x2, y2 = rectangle

        if enabled:
            background = config.GREEN
            border = config.GREEN_LIGHT
            status_text = "VALIDATE ENABLED"
            text_color = config.WHITE
        else:
            background = config.GRAY
            border = (150, 150, 150)
            status_text = "VALIDATE LOCKED"
            text_color = (215, 215, 215)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            background,
            -1,
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            border,
            5,
        )

        title_area = (
            x1,
            y1,
            x2,
            y1 + int((y2 - y1) * 0.58),
        )

        status_area = (
            x1,
            y1 + int((y2 - y1) * 0.50),
            x2,
            y2,
        )

        self._draw_centered_text(
            frame,
            title,
            title_area,
            1.0,
            text_color,
            3,
        )

        self._draw_centered_text(
            frame,
            status_text,
            status_area,
            0.62,
            text_color,
            2,
        )

    @staticmethod
    def _point_inside(
        x: int,
        y: int,
        rectangle: tuple[int, int, int, int] | None,
    ) -> bool:
        if rectangle is None:
            return False

        x1, y1, x2, y2 = rectangle

        return x1 <= x <= x2 and y1 <= y <= y2

    def _mouse_callback(
        self,
        event: int,
        x: int,
        y: int,
        flags: int,
        parameter: Any,
    ) -> None:
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        if self._point_inside(
            x,
            y,
            self.left_button,
        ):
            self.last_message = "VALIDATE ZONA KIRI DIKLIK"
            self.last_message_time = time.time()

        elif self._point_inside(
            x,
            y,
            self.right_button,
        ):
            self.last_message = "VALIDATE ZONA KANAN DIKLIK"
            self.last_message_time = time.time()

    @staticmethod
    def _zone_text(
        decision: Any,
    ) -> tuple[str, str, tuple[int, int, int]]:
        if not decision.forklift_detected:
            return (
                "FORKLIFT TIDAK ADA",
                "VALIDATE TERKUNCI",
                config.RED_LIGHT,
            )

        if not decision.within_distance:
            return (
                "FORKLIFT DI LUAR ZONA",
                "VALIDATE TERKUNCI",
                config.RED_LIGHT,
            )

        if decision.zone == "LEFT" and decision.loaded:
            return (
                "FORKLIFT BERMUATAN",
                "VALIDATE TERKUNCI",
                config.RED_LIGHT,
            )

        if decision.can_validate:
            return (
                "FORKLIFT TERDETEKSI",
                "VALIDATE SIAP",
                config.GREEN_LIGHT,
            )

        return (
            "VALIDATE TERKUNCI",
            decision.status,
            config.RED_LIGHT,
        )

    def render(
        self,
        camera_frame: np.ndarray,
        detections: list[dict[str, Any]],
        decisions: dict[str, Any],
        fps: float,
        inference_ms: float,
    ) -> np.ndarray:
        window_width = self.desktop_width
        window_height = self.desktop_height

        header_height = max(
            75,
            int(window_height * config.HEADER_HEIGHT_PERCENT),
        )

        camera_area_top = header_height
        camera_area_bottom = int(
            window_height * config.CAMERA_AREA_PERCENT
        )

        camera_area_height = (
            camera_area_bottom - camera_area_top
        )

        center_x = window_width // 2

        button_area_top = camera_area_bottom + 15
        button_area_bottom = window_height - 25

        resized_camera = cv2.resize(
            camera_frame,
            (
                window_width,
                camera_area_height,
            ),
            interpolation=cv2.INTER_LINEAR,
        )

        canvas = np.zeros(
            (
                window_height,
                window_width,
                3,
            ),
            dtype=np.uint8,
        )

        canvas[:] = config.DARK

        canvas[
            camera_area_top:camera_area_bottom,
            0:window_width,
        ] = resized_camera

        source_height, source_width = camera_frame.shape[:2]

        scale_x = window_width / source_width
        scale_y = camera_area_height / source_height

        left_decision = decisions["LEFT"]
        right_decision = decisions["RIGHT"]

        left_border = (
            config.GREEN
            if left_decision.can_validate
            else config.RED
        )

        right_border = (
            config.GREEN
            if right_decision.can_validate
            else config.RED
        )

        cv2.rectangle(
            canvas,
            (10, camera_area_top + 5),
            (center_x - 7, camera_area_bottom - 5),
            left_border,
            7,
        )

        cv2.rectangle(
            canvas,
            (center_x + 7, camera_area_top + 5),
            (window_width - 10, camera_area_bottom - 5),
            right_border,
            7,
        )

        cv2.line(
            canvas,
            (center_x, camera_area_top),
            (center_x, camera_area_bottom),
            config.YELLOW,
            4,
        )

        cv2.rectangle(
            canvas,
            (0, 0),
            (window_width, header_height),
            config.DARK,
            -1,
        )

        cv2.putText(
            canvas,
            f"{config.PROJECT_NAME} v{config.VERSION}",
            (30, int(header_height * 0.68)),
            cv2.FONT_HERSHEY_SIMPLEX,
            max(0.8, window_width / 1500),
            config.WHITE,
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            f"MAX DISTANCE: {config.MAX_DISTANCE:.1f} M",
            (
                int(window_width * 0.50),
                int(header_height * 0.68),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            config.YELLOW,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            f"YOLO {inference_ms:.0f} ms",
            (
                window_width - 365,
                int(header_height * 0.68),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            config.WHITE,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            f"FPS {fps:.1f}",
            (
                window_width - 155,
                int(header_height * 0.68),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            config.GREEN_LIGHT,
            2,
            cv2.LINE_AA,
        )

        for item in detections:
            source_x1, source_y1, source_x2, source_y2 = (
                item["bbox"]
            )

            x1 = int(source_x1 * scale_x)
            y1 = (
                camera_area_top
                + int(source_y1 * scale_y)
            )
            x2 = int(source_x2 * scale_x)
            y2 = (
                camera_area_top
                + int(source_y2 * scale_y)
            )

            if not item["within_distance"]:
                color = config.RED
                load_text = "OUTSIDE RANGE"
            elif item["loaded"]:
                color = config.YELLOW
                load_text = "LOADED"
            else:
                color = config.BLUE
                load_text = "EMPTY"

            distance = item.get("distance")

            distance_text = (
                f"{distance:.2f} m"
                if distance is not None
                else "unknown"
            )

            label = (
                f'{item["class_name"]} '
                f'{item["confidence"]:.2f} | '
                f'{item["zone"]} | '
                f'{load_text} | '
                f'{distance_text}'
            )

            cv2.rectangle(
                canvas,
                (x1, y1),
                (x2, y2),
                color,
                4,
            )

            cv2.putText(
                canvas,
                label,
                (x1, max(camera_area_top + 30, y1 - 12)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                color,
                2,
                cv2.LINE_AA,
            )

        left_title, left_detail, left_color = (
            self._zone_text(left_decision)
        )

        right_title, right_detail, right_color = (
            self._zone_text(right_decision)
        )

        left_panel = (
            35,
            camera_area_top + 20,
            center_x - 35,
            camera_area_top + 140,
        )

        right_panel = (
            center_x + 35,
            camera_area_top + 20,
            window_width - 35,
            camera_area_top + 140,
        )

        self._draw_transparent_panel(
            canvas,
            left_panel,
        )

        self._draw_transparent_panel(
            canvas,
            right_panel,
        )

        cv2.putText(
            canvas,
            "ZONA KIRI",
            (
                left_panel[0] + 25,
                left_panel[1] + 40,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            config.WHITE,
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            left_title,
            (
                left_panel[0] + 25,
                left_panel[1] + 78,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.66,
            left_color,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            left_detail,
            (
                left_panel[0] + 25,
                left_panel[1] + 108,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            left_color,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            "ZONA KANAN",
            (
                right_panel[0] + 25,
                right_panel[1] + 40,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            config.WHITE,
            3,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            right_title,
            (
                right_panel[0] + 25,
                right_panel[1] + 78,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.66,
            right_color,
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            canvas,
            right_detail,
            (
                right_panel[0] + 25,
                right_panel[1] + 108,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            right_color,
            2,
            cv2.LINE_AA,
        )

        button_margin = config.BUTTON_MARGIN
        center_gap = config.CENTER_GAP

        self.left_button = (
            button_margin,
            button_area_top,
            center_x - center_gap,
            button_area_bottom,
        )

        self.right_button = (
            center_x + center_gap,
            button_area_top,
            window_width - button_margin,
            button_area_bottom,
        )

        self._draw_button(
            canvas,
            self.left_button,
            "VALIDATE KIRI",
            left_decision.can_validate,
        )

        self._draw_button(
            canvas,
            self.right_button,
            "VALIDATE KANAN",
            right_decision.can_validate,
        )

        if (
            time.time() - self.last_message_time
            <= 3.0
        ):
            message_box = (
                center_x - 390,
                camera_area_bottom - 70,
                center_x + 390,
                camera_area_bottom - 15,
            )

            self._draw_transparent_panel(
                canvas,
                message_box,
                color=(0, 0, 0),
                alpha=0.88,
            )

            self._draw_centered_text(
                canvas,
                self.last_message,
                message_box,
                0.80,
                config.YELLOW,
                2,
            )

        return canvas

    def show(
        self,
        frame: np.ndarray,
    ) -> int:
        cv2.imshow(
            self.window_name,
            frame,
        )

        return cv2.waitKey(1) & 0xFF

    def toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen

        cv2.setWindowProperty(
            self.window_name,
            cv2.WND_PROP_FULLSCREEN,
            (
                cv2.WINDOW_FULLSCREEN
                if self.fullscreen
                else cv2.WINDOW_NORMAL
            ),
        )

    @staticmethod
    def close() -> None:
        cv2.destroyAllWindows()