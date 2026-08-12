"""
Entry point Smart Barrier Gate AI.

Alur:
Camera -> YOLO -> Decision Logic -> Odoo Bridge -> UI
"""

import time

import config
from button_logic import ButtonLogic
from camera import Camera
from detector import Detector
from odoo_bridge import OdooBridge
from ui import SmartGateUI


DEBUG_INTERVAL_SECONDS = 1.0


def print_debug(
    detections,
    decisions,
) -> None:
    print()
    print("=" * 70)
    print("DEBUG SMART GATE")
    print("=" * 70)

    if detections:
        print("DETECTIONS:")

        for index, item in enumerate(
            detections,
            start=1,
        ):
            print(
                f"[{index}] "
                f"class={item.get('class_name')} | "
                f"zone={item.get('zone')} | "
                f"distance={item.get('distance')} | "
                f"within_distance={item.get('within_distance')} | "
                f"loaded={item.get('loaded')} | "
                f"red_percent={item.get('red_percent')} | "
                f"confidence={item.get('confidence')}"
            )
    else:
        print("DETECTIONS: KOSONG")

    left = decisions["LEFT"]
    right = decisions["RIGHT"]

    print()
    print("LEFT DECISION:")
    print(
        f"forklift_detected={left.forklift_detected} | "
        f"within_distance={left.within_distance} | "
        f"loaded={left.loaded} | "
        f"can_validate={left.can_validate} | "
        f"odoo_validated={left.odoo_validated} | "
        f"gate_open={left.gate_open}"
    )
    print(f"status={left.status}")

    print()
    print("RIGHT DECISION:")
    print(
        f"forklift_detected={right.forklift_detected} | "
        f"within_distance={right.within_distance} | "
        f"loaded={right.loaded} | "
        f"can_validate={right.can_validate} | "
        f"odoo_validated={right.odoo_validated} | "
        f"gate_open={right.gate_open}"
    )
    print(f"status={right.status}")

    print("=" * 70)


def main() -> None:
    camera = None
    ui = None

    try:
        camera = Camera()
        detector = Detector()
        logic = ButtonLogic()
        ui = SmartGateUI()

        odoo_bridge = OdooBridge(
            host=config.API_HOST,
            port=config.API_PORT,
        )

        fps = 0.0
        previous_time = time.perf_counter()
        last_debug_time = 0.0

        last_left_gate_state = False
        last_right_gate_state = False

        odoo_bridge.start()
        camera.start()

        print("=" * 60)
        print(f"{config.PROJECT_NAME} v{config.VERSION}")
        print("=" * 60)
        print("Program aktif")
        print("Q / ESC = keluar")
        print("F       = fullscreen / windowed")
        print()
        print("API:")
        print(
            f"GET  http://127.0.0.1:"
            f"{config.API_PORT}/api/gate/status"
        )
        print(
            f"POST http://127.0.0.1:"
            f"{config.API_PORT}/api/gate/validate"
        )
        print("=" * 60)

        while True:
            frame = camera.read()

            if frame is None:
                print("Frame kamera tidak tersedia.")
                break

            # ------------------------------------------------
            # YOLO DETECTION
            # ------------------------------------------------

            inference_start = time.perf_counter()

            detections = detector.detect(
                frame=frame,
                classes=[config.CLASS_BOTTLE],
            )

            inference_ms = (
                time.perf_counter()
                - inference_start
            ) * 1000.0

            # ------------------------------------------------
            # STATUS VALIDATE DARI ODOO BRIDGE
            # ------------------------------------------------

            left_odoo_validated = (
                odoo_bridge.get_odoo_validated(
                    "LEFT"
                )
            )

            right_odoo_validated = (
                odoo_bridge.get_odoo_validated(
                    "RIGHT"
                )
            )

            # ------------------------------------------------
            # DECISION LOGIC
            # ------------------------------------------------

            decisions = logic.evaluate_all(
                detections=detections,
                left_odoo_validated=(
                    left_odoo_validated
                ),
                right_odoo_validated=(
                    right_odoo_validated
                ),
            )

            # ------------------------------------------------
            # UPDATE STATUS API
            # ------------------------------------------------

            odoo_bridge.update_decisions(
                decisions
            )

            # ------------------------------------------------
            # DEBUG TERMINAL
            # ------------------------------------------------

            current_wall_time = time.time()

            if (
                current_wall_time
                - last_debug_time
                >= DEBUG_INTERVAL_SECONDS
            ):
                print_debug(
                    detections=detections,
                    decisions=decisions,
                )

                last_debug_time = current_wall_time

            # ------------------------------------------------
            # HITUNG FPS
            # ------------------------------------------------

            current_time = time.perf_counter()
            elapsed = current_time - previous_time

            if elapsed > 0:
                current_fps = 1.0 / elapsed

                fps = (
                    fps * 0.90
                    + current_fps * 0.10
                )

            previous_time = current_time

            # ------------------------------------------------
            # RENDER UI
            # ------------------------------------------------

            output_frame = ui.render(
                camera_frame=frame,
                detections=detections,
                decisions=decisions,
                fps=fps,
                inference_ms=inference_ms,
            )

            key = ui.show(
                output_frame
            )

            if key in (
                ord("q"),
                27,
            ):
                break

            if key == ord("f"):
                ui.toggle_fullscreen()

            # ------------------------------------------------
            # STATUS GATE
            # ------------------------------------------------

            left_gate_open = (
                odoo_bridge.get_gate_open(
                    "LEFT"
                )
            )

            right_gate_open = (
                odoo_bridge.get_gate_open(
                    "RIGHT"
                )
            )

            if (
                left_gate_open
                and not last_left_gate_state
            ):
                print(
                    "GATE KIRI: OPEN COMMAND READY"
                )

            if (
                right_gate_open
                and not last_right_gate_state
            ):
                print(
                    "GATE KANAN: OPEN COMMAND READY"
                )

            last_left_gate_state = (
                left_gate_open
            )

            last_right_gate_state = (
                right_gate_open
            )

    except KeyboardInterrupt:
        print(
            "Program dihentikan oleh pengguna."
        )

    except Exception as error:
        print(
            f"ERROR: {type(error).__name__}: {error}"
        )

    finally:
        if camera is not None:
            camera.release()

        if ui is not None:
            ui.close()

        print(
            "Program ditutup."
        )


if __name__ == "__main__":
    main()