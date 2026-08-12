import cv2

from camera import Camera
from finger_detector import FingerDetector


def main():

    camera = Camera()
    detector = FingerDetector()

    try:

        camera.start()

        print("=" * 60)
        print("SMART GATE FINGER TEST")
        print("=" * 60)
        print("1 jari = FORKLIFT TANPA MUATAN")
        print("2 jari = FORKLIFT + MUATAN")
        print("=" * 60)

        while True:

            frame = camera.read()

            if frame is None:
                continue

            detections = detector.detect(
                frame
            )

            output = detector.draw(
                frame,
                detections,
            )

            for item in detections:

                print(
                    f"ZONE={item['zone']} | "
                    f"JARI={item['finger_count']} | "
                    f"STATE={item['vehicle_state']}"
                )

            cv2.imshow(
                "Finger Detector",
                output,
            )

            key = cv2.waitKey(1) & 0xFF

            if key in (
                ord("q"),
                27,
            ):
                break

    finally:

        camera.release()
        detector.close()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()