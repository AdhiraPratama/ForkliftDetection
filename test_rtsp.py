import cv2

from camera import Camera


def main():

    camera = Camera()

    try:

        camera.start()

        print(
            "RTSP TEST BERJALAN"
        )

        print(
            "Q = keluar"
        )

        while True:

            frame = camera.read()

            if frame is None:

                continue

            cv2.imshow(
                "Hikvision RTSP Test",
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

    finally:

        camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":

    main()