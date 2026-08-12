"""
Logika izin validasi Odoo dan pembukaan barrier gate.

Penting:
- Deteksi forklift hanya memberikan izin validate.
- Gate hanya terbuka setelah Odoo mengirim status validate berhasil.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ZoneDecision:
    zone: str

    forklift_detected: bool
    within_distance: bool
    loaded: bool

    can_validate: bool
    odoo_validated: bool
    gate_open: bool

    status: str


class ButtonLogic:
    """
    Aturan sementara menggunakan bottle sebagai simulasi forklift.

    LEFT:
    - Bottle/forklift harus ada.
    - Jarak maksimal 5 meter.
    - Harus kosong/tanpa muatan.
    - Setelah Odoo validate berhasil, gate boleh terbuka.

    RIGHT:
    - Bottle/forklift harus ada.
    - Jarak maksimal 5 meter.
    - Boleh kosong atau bermuatan.
    - Setelah Odoo validate berhasil, gate boleh terbuka.
    """

    @staticmethod
    def _find_zone_objects(
        detections: list[dict[str, Any]],
        zone: str,
    ) -> list[dict[str, Any]]:
        return [
            detection
            for detection in detections
            if detection.get("zone") == zone
        ]

    def evaluate_zone(
        self,
        detections: list[dict[str, Any]],
        zone: str,
        odoo_validated: bool = False,
    ) -> ZoneDecision:
        zone = zone.upper()

        zone_objects = self._find_zone_objects(
            detections=detections,
            zone=zone,
        )

        valid_objects = [
            detection
            for detection in zone_objects
            if detection.get("within_distance", False)
        ]

        forklift_detected = len(valid_objects) > 0
        within_distance = forklift_detected

        # loaded=True saat simulasi bottle mendeteksi tutup/marker merah.
        loaded = any(
            detection.get("loaded", False)
            for detection in valid_objects
        )

        if zone == "LEFT":
            # Zona kiri hanya menerima forklift kosong.
            can_validate = (
                forklift_detected
                and within_distance
                and not loaded
            )

        elif zone == "RIGHT":
            # Zona kanan menerima forklift kosong maupun bermuatan.
            can_validate = (
                forklift_detected
                and within_distance
            )

        else:
            can_validate = False

        # Gate tidak boleh terbuka hanya karena forklift terdeteksi.
        # Harus ada validate berhasil dari Odoo.
        gate_open = (
            can_validate
            and odoo_validated
        )

        status = self._build_status(
            zone=zone,
            forklift_detected=forklift_detected,
            within_distance=within_distance,
            loaded=loaded,
            can_validate=can_validate,
            odoo_validated=odoo_validated,
            gate_open=gate_open,
        )

        return ZoneDecision(
            zone=zone,
            forklift_detected=forklift_detected,
            within_distance=within_distance,
            loaded=loaded,
            can_validate=can_validate,
            odoo_validated=odoo_validated,
            gate_open=gate_open,
            status=status,
        )

    @staticmethod
    def _build_status(
        zone: str,
        forklift_detected: bool,
        within_distance: bool,
        loaded: bool,
        can_validate: bool,
        odoo_validated: bool,
        gate_open: bool,
    ) -> str:
        if not forklift_detected:
            return "FORKLIFT TIDAK ADA - VALIDATE TERKUNCI"

        if not within_distance:
            return "FORKLIFT DI LUAR ZONA - VALIDATE TERKUNCI"

        if zone == "LEFT" and loaded:
            return "FORKLIFT BERMUATAN - VALIDATE TERKUNCI"

        if can_validate and not odoo_validated:
            return "FORKLIFT TERDETEKSI - MENUNGGU VALIDATE ODOO"

        if gate_open:
            return "VALIDATE BERHASIL - GATE OPEN"

        return "VALIDATE TERKUNCI"

    def evaluate_all(
        self,
        detections: list[dict[str, Any]],
        left_odoo_validated: bool = False,
        right_odoo_validated: bool = False,
    ) -> dict[str, ZoneDecision]:
        return {
            "LEFT": self.evaluate_zone(
                detections=detections,
                zone="LEFT",
                odoo_validated=left_odoo_validated,
            ),
            "RIGHT": self.evaluate_zone(
                detections=detections,
                zone="RIGHT",
                odoo_validated=right_odoo_validated,
            ),
        }