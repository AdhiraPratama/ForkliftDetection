import cv2

import config
from camera import Camera
from detector import Detector


def main() -> None:
    camera = Camera()
    detector = Detector()

    try:
        camera.start()

        print("Kamera dan detector berhasil dibuka.")

        while True:
            frame = camera.read()

            if frame is None:
                print("Frame kosong.")
                break

            detections = detector.detect(
                frame,
                classes=[config.CLASS_BOTTLE],
            )

            for item in detections:
                x1, y1, x2, y2 = item["bbox"]

                if item["loaded"]:
                    color = (0, 255, 255)
                    load_text = "LOADED"
                else:
                    color = (255, 170, 0)
                    load_text = "EMPTY"

                if item["distance"] is not None:
                    distance_text = (
                        f'{item["distance"]:.2f} m'
                    )
                else:
                    distance_text = "unknown"

                label = (
                    f'{item["class_name"]} '
                    f'{item["confidence"]:.2f} | '
                    f'{item["zone"]} | '
                    f'{load_text} | '
                    f'{distance_text}'
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2,
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, max(25, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                )

                print(item)

            center_x = frame.shape[1] // 2

            cv2.line(
                frame,
                (center_x, 0),
                (center_x, frame.shape[0]),
                (0, 255, 255),
                2,
            )

            cv2.imshow(
                "Detector Test",
                frame,
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except Exception as error:
        print(f"ERROR: {error}")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Program ditutup.")


if __name__ == "__main__":
    main()