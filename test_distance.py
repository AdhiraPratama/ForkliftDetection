from distance import (
    calculate_focal_length,
    estimate_distance,
    is_within_limit,
)


def main():
    real_height = 0.25
    known_distance = 2.0
    object_height_pixels = 100

    focal_length = calculate_focal_length(
        object_height_pixels=object_height_pixels,
        known_distance_meters=known_distance,
        real_height_meters=real_height,
    )

    distance = estimate_distance(
        object_height_pixels=100,
        real_height_meters=real_height,
        focal_length_pixels=focal_length,
    )

    within_limit = is_within_limit(
        distance_meters=distance,
        max_distance_meters=5.0,
    )

    print(f"Focal length: {focal_length:.2f} px")
    print(f"Estimasi jarak: {distance:.2f} m")
    print(f"Di bawah 5 meter: {within_limit}")


if __name__ == "__main__":
    main()