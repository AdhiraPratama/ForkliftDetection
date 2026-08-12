from pathlib import Path

from ultralytics import YOLO


OUTPUT_FOLDER = Path("yolo11n_openvino_model")

if OUTPUT_FOLDER.exists():
    print("Model OpenVINO sudah tersedia:")
    print(OUTPUT_FOLDER.resolve())
else:
    print("Memuat YOLO11n...")

    model = YOLO("yolo11n.pt")

    hasil = model.export(
        format="openvino",
        imgsz=320,
        half=False,
        dynamic=False,
    )

    print("Export selesai:")
    print(hasil)