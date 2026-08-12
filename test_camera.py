import cv2

from camera import Camera


def main():
    camera = Camera()

    try:
        camera.start()
        print("Camera berhasil dibuka.")

        while True:
            frame = camera.read()

            if frame is None:
                print("Frame kosong.")
                break

            cv2.imshow("Camera Test", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    except Exception as error:
        print(f"ERROR: {error}")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Camera ditutup.")


if __name__ == "__main__":
    main()