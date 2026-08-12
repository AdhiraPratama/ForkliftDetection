import time

from mqtt_gate import MQTTGate


def main() -> None:
    mqtt_gate = MQTTGate()

    try:
        connected = mqtt_gate.start()

        if not connected:
            print("Gagal terhubung ke broker.")
            return

        print("MQTT berhasil terhubung.")

        mqtt_gate.publish_event(
            event_name="PYTHON_ONLINE",
            data={
                "message": (
                    "Smart Gate Python aktif"
                )
            },
        )

        time.sleep(1)

        mqtt_gate.open_gate(
            zone="LEFT",
            source="PYTHON_TEST",
            reference="TEST-001",
        )

        print(
            "Command OPEN sudah dikirim."
        )

        time.sleep(5)

    finally:
        mqtt_gate.stop()


if __name__ == "__main__":
    main()