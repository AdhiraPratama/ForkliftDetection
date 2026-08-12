"""
HTTP API penghubung Smart Barrier Gate AI dengan Odoo.

Endpoint:
GET  /api/gate/status
POST /api/gate/validate
POST /api/gate/reset
"""

from __future__ import annotations

from threading import Lock, Thread
from typing import Any

from flask import Flask, jsonify, request


class OdooBridge:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
    ) -> None:
        self.host = host
        self.port = port

        self.app = Flask(__name__)
        self.lock = Lock()

        self.zone_state: dict[str, dict[str, Any]] = {
            "LEFT": self._default_zone_state(),
            "RIGHT": self._default_zone_state(),
        }

        self._register_routes()

    @staticmethod
    def _default_zone_state() -> dict[str, Any]:
        return {
            "forklift_detected": False,
            "within_distance": False,
            "loaded": False,
            "can_validate": False,
            "odoo_validated": False,
            "gate_open": False,
            "status": "Belum ada data",
        }

    def update_decisions(
        self,
        decisions: dict[str, Any],
    ) -> None:
        """
        Dipanggil terus dari app.py untuk memperbarui
        kondisi hasil deteksi AI.
        """

        with self.lock:
            for zone in ("LEFT", "RIGHT"):
                decision = decisions[zone]

                previous_validated = self.zone_state[zone][
                    "odoo_validated"
                ]

                self.zone_state[zone] = {
                    "forklift_detected": (
                        decision.forklift_detected
                    ),
                    "within_distance": (
                        decision.within_distance
                    ),
                    "loaded": decision.loaded,
                    "can_validate": decision.can_validate,
                    "odoo_validated": previous_validated,
                    "gate_open": (
                        decision.can_validate
                        and previous_validated
                    ),
                    "status": decision.status,
                }

                # Reset otomatis jika objek sudah tidak valid.
                if not decision.can_validate:
                    self.zone_state[zone][
                        "odoo_validated"
                    ] = False

                    self.zone_state[zone][
                        "gate_open"
                    ] = False

    def get_odoo_validated(
        self,
        zone: str,
    ) -> bool:
        zone = zone.upper()

        with self.lock:
            return bool(
                self.zone_state.get(
                    zone,
                    {},
                ).get(
                    "odoo_validated",
                    False,
                )
            )

    def get_gate_open(
        self,
        zone: str,
    ) -> bool:
        zone = zone.upper()

        with self.lock:
            return bool(
                self.zone_state.get(
                    zone,
                    {},
                ).get(
                    "gate_open",
                    False,
                )
            )

    def get_all_states(
        self,
    ) -> dict[str, dict[str, Any]]:
        with self.lock:
            return {
                zone: dict(state)
                for zone, state in self.zone_state.items()
            }

    def _register_routes(self) -> None:
        @self.app.get("/api/gate/status")
        def gate_status():
            return jsonify(
                {
                    "success": True,
                    "zones": self.get_all_states(),
                }
            )

        @self.app.get("/api/gate/status/<zone>")
        def zone_status(zone: str):
            zone = zone.upper()

            if zone not in ("LEFT", "RIGHT"):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Zone harus LEFT atau RIGHT",
                        }
                    ),
                    400,
                )

            with self.lock:
                state = dict(self.zone_state[zone])

            return jsonify(
                {
                    "success": True,
                    "zone": zone,
                    "data": state,
                }
            )

        @self.app.post("/api/gate/validate")
        def validate_gate():
            payload = request.get_json(
                silent=True,
            ) or {}

            zone = str(
                payload.get("zone", "")
            ).upper()

            reference = payload.get(
                "reference",
            )

            if zone not in ("LEFT", "RIGHT"):
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Zone harus LEFT atau RIGHT",
                        }
                    ),
                    400,
                )

            with self.lock:
                state = self.zone_state[zone]

                if not state["can_validate"]:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "zone": zone,
                                "reference": reference,
                                "message": (
                                    "Validate ditolak karena "
                                    "forklift tidak memenuhi kondisi"
                                ),
                                "data": dict(state),
                            }
                        ),
                        409,
                    )

                state["odoo_validated"] = True
                state["gate_open"] = True
                state["status"] = (
                    "VALIDATE BERHASIL - GATE OPEN"
                )

                response_state = dict(state)

            return jsonify(
                {
                    "success": True,
                    "zone": zone,
                    "reference": reference,
                    "message": (
                        "Validate diterima dan gate diizinkan terbuka"
                    ),
                    "data": response_state,
                }
            )

        @self.app.post("/api/gate/reset")
        def reset_gate():
            payload = request.get_json(
                silent=True,
            ) or {}

            zone = str(
                payload.get("zone", "")
            ).upper()

            zones = (
                [zone]
                if zone in ("LEFT", "RIGHT")
                else ["LEFT", "RIGHT"]
            )

            with self.lock:
                for current_zone in zones:
                    self.zone_state[current_zone][
                        "odoo_validated"
                    ] = False

                    self.zone_state[current_zone][
                        "gate_open"
                    ] = False

                    self.zone_state[current_zone][
                        "status"
                    ] = "Validate di-reset"

            return jsonify(
                {
                    "success": True,
                    "message": "Status validate berhasil di-reset",
                    "zones": zones,
                }
            )

    def start(self) -> None:
        server_thread = Thread(
            target=self.app.run,
            kwargs={
                "host": self.host,
                "port": self.port,
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
        )

        server_thread.start()

        print(
            f"Odoo Bridge aktif di "
            f"http://127.0.0.1:{self.port}"
        )