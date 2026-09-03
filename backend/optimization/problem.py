from dataclasses import dataclass


@dataclass
class ProblemInstance:
    distance_matrix: list
    vehicles: list
    customers: list
    # Optional road-network data.  Existing matrix-only scenarios leave these
    # as None and therefore preserve their original distance objective.
    travel_time_matrix: list | None = None
    metadata: dict | None = None
