from local_search import two_opt
from qpso import QPSO
from fitness import fitness
from constraints import validate


def hybrid_qpso(problem, num_particles=10, iterations=20, beta=0.5):

    # Step 1: Run QPSO
    qpso = QPSO(
        num_particles=num_particles,
        num_customers=len(problem.customers)
    )

    for _ in range(iterations):
        qpso.step(
            problem,
            fitness,
            beta=beta
        )

    # Get QPSO's best solution
    qpso_result = qpso.get_best_solution(problem)

    if qpso_result is None:
        return None

    # Step 2: Improve QPSO solution using 2-opt
    improved_routes, improved_score = two_opt(
        qpso_result["routes"],
        problem,
        fitness
    )

    # Make sure the final solution is valid
    if not validate(improved_routes, problem):
        return {
            "algorithm": "Hybrid QPSO + 2-opt",
            "routes": qpso_result["routes"],
            "fitness": qpso_result["fitness"]
        }

    return {
        "algorithm": "Hybrid QPSO + 2-opt",
        "routes": improved_routes,
        "fitness": improved_score
    }

if __name__ == "__main__":

    from problem import ProblemInstance

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]

    problem = ProblemInstance(
        distance_matrix=distance_matrix,

        vehicles=[
            {"id": 1, "capacity": 10},
            {"id": 2, "capacity": 10}
        ],

        customers=[
            {"id": 1, "demand": 2},
            {"id": 2, "demand": 3},
            {"id": 3, "demand": 1},
            {"id": 4, "demand": 2}
        ]
    )

    result = hybrid_qpso(problem)

    print("\nHybrid Result")
    print("-------------")
    print("Routes:", result["routes"])
    print("Fitness:", result["fitness"])