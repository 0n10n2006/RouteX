from dataclasses import dataclass


@dataclass
class OptimizationResult:

    algorithm: str
    routes: list
    fitness: float
    distance: float
    runtime: float


if __name__ == "__main__":

    result = OptimizationResult(
        algorithm="QPSO",
        routes=[
            [0, 1, 2, 0],
            [0, 3, 4, 0]
        ],
        fitness=84,
        distance=84,
        runtime=0.12
    )

    print(result)