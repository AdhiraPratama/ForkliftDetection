"""
MQTT communication untuk Smart Barrier Gate AI.
"""

from __future__ import annotations

import json
from datetime import datetime
from threading import Event, Lock
from typing import Any

import paho.mqtt.client as mqtt

import config


class MQTTGate:
    def __init__(self) -> None:
        self.connected = False
        self.connected_event = Event()
        self.lock = Lock()

        self.esp32_status: dict[str, Any] = {}
        self.esp32_heartbeat: dict[str, Any] = {}
        self.emergency_status: dict[str, Any] = {}

        self.client = mqtt.Client(
            callback_api_version=(
                mqtt.CallbackAPIVersion.VERSION2
            ),
            client_id=config.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311,
        )

        if config.MQTT_USERNAME:
            self.client.username_pw_set(
                username=config.MQTT_USERNAME,
                password=config.MQTT_PASSWORD,
            )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.client.reconnect_delay_set(
            min_delay=1,
            max_delay=10,
        )

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        if reason_code.is_failure:
            self.connected = False
            self.connected_event.clear()

            print(
                f"MQTT gagal terhubung: {reason_code}"
            )
            return

        self.connected = True
        self.connected_event.set()

        print(
            f"MQTT terhubung ke "
            f"{config.MQTT_BROKER}:"
            f"{config.MQTT_PORT}"
        )

        client.subscribe(
            config.MQTT_TOPIC_STATUS,
            qos=config.MQTT_QOS,
        )

        client.subscribe(
            config.MQTT_TOPIC_HEARTBEAT,
            qos=config.MQTT_QOS,
        )

        client.subscribe(
            config.MQTT_TOPIC_EMERGENCY,
            qos=config.MQTT_QOS,
        )

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: mqtt.DisconnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None,
    ) -> None:
        self.connected = False
        self.connected_event.clear()

        print(
            f"MQTT terputus: {reason_code}"
        )

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        try:
            payload = json.loads(
                message.payload.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            print(
                f"Payload MQTT tidak valid: "
                f"{message.topic}"
            )
            return

        with self.lock:
            if (
                message.topic
                == config.MQTT_TOPIC_STATUS
            ):
                self.esp32_status = payload

            elif (
                message.topic
                == config.MQTT_TOPIC_HEARTBEAT
            ):
                self.esp32_heartbeat = payload

            elif (
                message.topic
                == config.MQTT_TOPIC_EMERGENCY
            ):
                self.emergency_status = payload

        print()
        print("MQTT RX")
        print(f"Topic   : {message.topic}")
        print(f"Payload : {payload}")

    def start(
        self,
        wait_seconds: float = 5.0,
    ) -> bool:
        self.client.connect_async(
            host=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            keepalive=config.MQTT_KEEPALIVE,
        )

        self.client.loop_start()

        return self.connected_event.wait(
            timeout=wait_seconds
        )

    def stop(self) -> None:
        try:
            if self.connected:
                self.client.disconnect()
        finally:
            self.client.loop_stop()

    def _publish(
        self,
        topic: str,
        payload: dict[str, Any],
        retain: bool = False,
    ) -> bool:
        if not self.connected:
            print(
                f"MQTT publish dibatalkan, "
                f"belum terhubung: {topic}"
            )
            return False

        payload_text = json.dumps(
            payload,
            ensure_ascii=False,
        )

        result = self.client.publish(
            topic=topic,
            payload=payload_text,
            qos=config.MQTT_QOS,
            retain=retain,
        )

        return (
            result.rc
            == mqtt.MQTT_ERR_SUCCESS
        )

    def publish_ai_status(
        self,
        detections: list[dict[str, Any]],
        decisions: dict[str, Any],
    ) -> bool:
        left = decisions["LEFT"]
        right = decisions["RIGHT"]

        payload = {
            "gate": config.MQTT_GATE_ID,
            "timestamp": datetime.now().isoformat(),
            "detections": detections,
            "zones": {
                "LEFT": {
                    "forklift_detected": (
                        left.forklift_detected
                    ),
                    "within_distance": (
                        left.within_distance
                    ),
                    "loaded": left.loaded,
                    "can_validate": (
                        left.can_validate
                    ),
                    "status": left.status,
                },
                "RIGHT": {
                    "forklift_detected": (
                        right.forklift_detected
                    ),
                    "within_distance": (
                        right.within_distance
                    ),
                    "loaded": right.loaded,
                    "can_validate": (
                        right.can_validate
                    ),
                    "status": right.status,
                },
            },
        }

        return self._publish(
            topic=config.MQTT_TOPIC_AI,
            payload=payload,
            retain=False,
        )

    def publish_validate_status(
        self,
        zone: str,
        validated: bool,
        reference: str = "",
    ) -> bool:
        return self._publish(
            topic=config.MQTT_TOPIC_VALIDATE,
            payload={
                "gate": config.MQTT_GATE_ID,
                "zone": zone.upper(),
                "validated": validated,
                "reference": reference,
                "timestamp": (
                    datetime.now().isoformat()
                ),
            },
            retain=False,
        )

    def open_gate(
        self,
        zone: str,
        source: str,
        reference: str = "",
    ) -> bool:
        return self._publish(
            topic=config.MQTT_TOPIC_COMMAND,
            payload={
                "gate": config.MQTT_GATE_ID,
                "zone": zone.upper(),
                "command": "OPEN",
                "source": source,
                "reference": reference,
                "timestamp": (
                    datetime.now().isoformat()
                ),
            },
            retain=False,
        )

    def publish_event(
        self,
        event_name: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        return self._publish(
            topic=config.MQTT_TOPIC_EVENT,
            payload={
                "gate": config.MQTT_GATE_ID,
                "event": event_name,
                "data": data or {},
                "timestamp": (
                    datetime.now().isoformat()
                ),
            },
            retain=False,
        )

    def get_esp32_status(
        self,
    ) -> dict[str, Any]:
        with self.lock:
            return dict(self.esp32_status)

    def get_heartbeat(
        self,
    ) -> dict[str, Any]:
        with self.lock:
            return dict(self.esp32_heartbeat)