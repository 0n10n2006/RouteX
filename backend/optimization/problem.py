from dataclasses import dataclass


@dataclass
class ProblemInstance:
    distance_matrix: list
    vehicles: list
    customers: list

