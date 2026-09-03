from .local_search import two_opt
from .qpso import QPSO
from .fitness import fitness
from .constraints import validate


def hybrid_qpso(
    problem,
    num_particles=10,
    iterations=20,
    beta=0.5
):
    """
    Adaptive Hybrid QPSO + 2-opt.

    QPSO performs the global search.
    2-opt is triggered whenever QPSO discovers
    a new global best solution.

    The locally improved solution is kept externally
    as the best hybrid solution, but is NOT injected
    back into the QPSO swarm.

    This architecture was selected after Week 4
    ablation experiments showed that feedback injection
    consistently underperformed plain QPSO + 2-opt.
    """

    qpso = QPSO(
        num_particles=num_particles,
        num_customers=len(problem.customers)
    )

    best_routes = None
    best_score = float("inf")

    previous_qpso_best = float("inf")

    local_search_count = 0

    for _ in range(iterations):

        # Run one QPSO iteration.
        qpso.step(
            problem,
            fitness,
            beta=beta
        )

        current_qpso_best = qpso.global_best_fitness

        # Apply local search only when QPSO
        # discovers a new global best.
        if current_qpso_best < previous_qpso_best:

            qpso_result = qpso.get_best_solution(problem)

            if qpso_result is not None:

                candidate_routes = qpso_result["routes"]
                candidate_score = qpso_result["fitness"]

                improved_routes, improved_score = two_opt(
                    candidate_routes,
                    problem,
                    fitness
                )

                local_search_count += 1

                # Never allow 2-opt to worsen the solution.
                if improved_score > candidate_score:
                    improved_routes = candidate_routes
                    improved_score = candidate_score

                # Keep the best hybrid solution found so far.
                if improved_score < best_score:

                    best_routes = [
                        route[:]
                        for route in improved_routes
                    ]

                    best_score = improved_score

            previous_qpso_best = current_qpso_best

    # Fallback if no QPSO solution was recorded.
    if best_routes is None:

        qpso_result = qpso.get_best_solution(problem)

        if qpso_result is None:
            return None

        best_routes = qpso_result["routes"]
        best_score = qpso_result["fitness"]

    # Final safety check.
    if not validate(best_routes, problem):

        qpso_result = qpso.get_best_solution(problem)

        if qpso_result is None:
            return None

        best_routes = qpso_result["routes"]
        best_score = qpso_result["fitness"]

    return {
        "algorithm": "Adaptive Hybrid QPSO + 2-opt",
        "routes": best_routes,
        "fitness": best_score,
        "convergence": qpso.convergence,
        "local_search_count": local_search_count
    }


if __name__ == "__main__":

    from .problem import ProblemInstance

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

    result = hybrid_qpso(
        problem,
        num_particles=5,
        iterations=20,
        beta=0.5
    )

    print("\n## Adaptive Hybrid QPSO + 2-opt Result")
    print("\nRoutes:", result["routes"])
    print("Fitness:", result["fitness"])
    print("Local search triggers:", result["local_search_count"])