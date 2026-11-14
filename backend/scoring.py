def calculate_score(
    brightness,
    cloudiness,
    edge_count
):

    brightness_score = min(
        100,
        int(brightness / 255 * 100)
    )

    cloudiness_score = min(
        100,
        int(cloudiness / 3)
    )

    # Edge count is currently too noisy,
    # so we use a much smaller impact.

    edge_score = max(
        0,
        100 - int(edge_count / 500)
    )

    final_score = int(
        brightness_score * 0.45 +
        cloudiness_score * 0.45 +
        edge_score * 0.10
    )

    return final_score