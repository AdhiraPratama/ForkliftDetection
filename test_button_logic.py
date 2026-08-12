from button_logic import ButtonLogic


def print_result(title, result):
    print()
    print("=" * 55)
    print(title)
    print("=" * 55)

    print(f"Zone              : {result.zone}")
    print(f"Forklift detected : {result.forklift_detected}")
    print(f"Within distance   : {result.within_distance}")
    print(f"Loaded            : {result.loaded}")
    print(f"Can validate      : {result.can_validate}")
    print(f"Odoo validated    : {result.odoo_validated}")
    print(f"Gate open         : {result.gate_open}")
    print(f"Status            : {result.status}")


def main():
    logic = ButtonLogic()

    # Simulasi forklift kosong di zona kiri.
    left_empty = [
        {
            "class_name": "bottle",
            "zone": "LEFT",
            "distance": 2.0,
            "within_distance": True,
            "loaded": False,
        }
    ]

    # Belum validate Odoo.
    result = logic.evaluate_zone(
        detections=left_empty,
        zone="LEFT",
        odoo_validated=False,
    )

    print_result(
        "Forklift kosong - sebelum validate",
        result,
    )

    # Validate Odoo berhasil.
    result = logic.evaluate_zone(
        detections=left_empty,
        zone="LEFT",
        odoo_validated=True,
    )

    print_result(
        "Forklift kosong - setelah validate",
        result,
    )

    # Forklift bermuatan di zona kiri.
    left_loaded = [
        {
            "class_name": "bottle",
            "zone": "LEFT",
            "distance": 2.0,
            "within_distance": True,
            "loaded": True,
        }
    ]

    result = logic.evaluate_zone(
        detections=left_loaded,
        zone="LEFT",
        odoo_validated=True,
    )

    print_result(
        "Forklift bermuatan di zona kiri",
        result,
    )

    # Tidak ada forklift.
    result = logic.evaluate_zone(
        detections=[],
        zone="RIGHT",
        odoo_validated=True,
    )

    print_result(
        "Odoo validate tetapi forklift tidak ada",
        result,
    )


if __name__ == "__main__":
    main()