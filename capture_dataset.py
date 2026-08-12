from pathlib import Path
from datetime import datetime

import cv2


CAMERA_INDEX = 0
OUTPUT_FOLDER = Path("dataset_raw")

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30


OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Webcam tidak dapat dibuka.")
    raise SystemExit

camera.set(
    cv2.CAP_PROP_FOURCC,
    cv2.VideoWriter_fourcc(*"MJPG")
)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
camera.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

jumlah_foto = 0

print("SPACE = ambil foto")
print("Q = keluar")

while True:
    berhasil, frame = camera.read()

    if not berhasil:
        print("Gagal membaca webcam.")
        break

    tampilan = frame.copy()

    cv2.putText(
        tampilan,
        f"Foto tersimpan: {jumlah_foto}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        tampilan,
        "SPACE: Ambil Foto | Q: Keluar",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow("Pengambilan Dataset PPE", tampilan)

    tombol = cv2.waitKey(1) & 0xFF

    if tombol == ord("q"):
        break

    if tombol == 32:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        nama_file = OUTPUT_FOLDER / f"ppe_{timestamp}.jpg"

        cv2.imwrite(str(nama_file), frame)

        jumlah_foto += 1
        print(f"Disimpan: {nama_file}")

camera.release()
cv2.destroyAllWindows()

print(f"Total foto: {jumlah_foto}")