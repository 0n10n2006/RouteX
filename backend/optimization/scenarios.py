try:
    # When imported as part of the backend package (e.g. by the FastAPI app)
    from .problem import ProblemInstance
except ImportError:
    # When run directly from inside the optimization/ folder: python scenarios.py
    from problem import ProblemInstance


def create_scenarios():

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]

    vehicles = [
        {"id": 1, "capacity": 10},
        {"id": 2, "capacity": 10}
    ]

    scenarios = {

        "low": ProblemInstance(
            distance_matrix=distance_matrix,
            vehicles=vehicles,
            customers=[
                {"id": 1, "demand": 1},
                {"id": 2, "demand": 1},
                {"id": 3, "demand": 1},
                {"id": 4, "demand": 1}
            ]
        ),

        "medium": ProblemInstance(
            distance_matrix=distance_matrix,
            vehicles=vehicles,
            customers=[
                {"id": 1, "demand": 2},
                {"id": 2, "demand": 3},
                {"id": 3, "demand": 2},
                {"id": 4, "demand": 3}
            ]
        ),

        "high": ProblemInstance(
            distance_matrix=distance_matrix,
            vehicles=vehicles,
            customers=[
                {"id": 1, "demand": 4},
                {"id": 2, "demand": 4},
                {"id": 3, "demand": 3},
                {"id": 4, "demand": 3}
            ]
        )
    }

    return scenarios


if __name__ == "__main__":

    scenarios = create_scenarios()

    for name, problem in scenarios.items():

        print(
            name,
            "scenario:",
            len(problem.customers),
            "customers"
        )