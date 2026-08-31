# Week 2 - Traffic Model

TRAFFIC_FACTORS = {
    "Low": 1.0,
    "Medium": 1.3,
    "High": 1.7
}


def get_traffic_factor(traffic_level):
    """
    Return traffic multiplier based on traffic level.
    """

    if traffic_level not in TRAFFIC_FACTORS:
        raise ValueError(
            f"Invalid traffic level: {traffic_level}"
        )

    return TRAFFIC_FACTORS[traffic_level]


def calculate_travel_time(distance, traffic_level, base_speed=40):
    """
    Calculate travel time considering traffic.

    distance: distance in km
    traffic_level: Low / Medium / High
    base_speed: normal speed in km/h
    """

    factor = get_traffic_factor(traffic_level)

    effective_speed = base_speed / factor

    travel_time = distance / effective_speed

    return travel_time


if __name__ == "__main__":

    print("Traffic Model Test")
    print("==================")

    for level in TRAFFIC_FACTORS:
        factor = get_traffic_factor(level)
        time = calculate_travel_time(10, level)

        print(
            f"{level}: "
            f"Factor = {factor}, "
            f"10 km Travel Time = {time:.2f} hours"
        )