"""
Modul estimasi jarak objek dari tinggi bounding box.
"""


def estimate_distance(
    object_height_pixels: int,
    real_height_meters: float,
    focal_length_pixels: float,
) -> float | None:
    if object_height_pixels <= 0:
        return None

    return (
        real_height_meters
        * focal_length_pixels
        / object_height_pixels
    )


def is_within_limit(
    distance_meters: float | None,
    max_distance_meters: float,
) -> bool:
    return (
        distance_meters is not None
        and distance_meters <= max_distance_meters
    )


def calculate_focal_length(
    object_height_pixels: int,
    known_distance_meters: float,
    real_height_meters: float,
) -> float:
    if object_height_pixels <= 0:
        raise ValueError("Tinggi objek dalam pixel harus lebih dari 0.")

    if known_distance_meters <= 0:
        raise ValueError("Jarak kalibrasi harus lebih dari 0.")

    if real_height_meters <= 0:
        raise ValueError("Tinggi objek sebenarnya harus lebih dari 0.")

    return (
        object_height_pixels
        * known_distance_meters
        / real_height_meters
    )