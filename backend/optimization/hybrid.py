import random

from .local_search import iterated_local_search
from .qpso import QPSO
from .qpso_utils import decode_random_keys
from .repair import repair_solution
from .fitness import fitness
from .constraints import validate


def _anneal_beta(beta, iteration, iterations, beta_floor_ratio=0.4):
    """
    Linearly anneal beta from its starting value down to
    `beta_floor_ratio * beta` over the course of the run.

    A fixed beta gives QPSO a constant contraction-expansion coefficient
    for its whole run, so the swarm never settles down: high beta favors
    exploration (good early), low beta favors exploitation/convergence
    (good late). Annealing it means the swarm hands 2-opt/Or-opt better,
    more refined starting orderings by the time local search takes over,
    instead of the same noisy exploration-level positions throughout.
    """

    if iterations <= 1:
        return beta

    floor = beta * beta_floor_ratio

    progress = iteration / (iterations - 1)

    return beta - (beta - floor) * progress


def _decode_particle(particle, problem):
    """Decode a QPSO particle's personal-best position into VRP routes."""

    customer_order = decode_random_keys(particle.best_position)

    routes = repair_solution(customer_order, problem)

    if routes is None:
        return None

    return {"routes": routes, "fitness": particle.best_fitness}


def hybrid_qpso(
    problem,
    num_particles=10,
    iterations=20,
    beta=0.5,
    local_search_probability=1.0,
    top_k_particles=2,
    ils_max_kicks=4
):
    """
    Adaptive Hybrid QPSO + (2-opt / Or-opt / double-bridge) iterated local
    search.

    QPSO performs the global search, using an annealed beta so the swarm
    explores early and exploits late instead of wandering at a constant
    rate for the whole run.

    Whenever QPSO discovers a new global best, local search is applied
    (according to local_search_probability) not just to the single global
    best particle but to the top-K particles by personal-best fitness.
    Plain 2-opt can only reverse a segment in place, so it can get stuck
    exactly at a starting order it was handed even when a better ordering
    is one relocate move away; giving it several different starting
    points (top-K particles) and a richer move set (Or-opt) plus an
    escape hatch (a double-bridge kick when it stalls) makes it very
    unlikely all of them land in the same bad local optimum.

    The locally improved solution is kept externally as the best hybrid
    solution, but is NOT injected back into the QPSO swarm.
    """

    qpso = QPSO(
        num_particles=num_particles,
        num_customers=len(problem.customers)
    )

    best_routes = None
    best_score = float("inf")

    previous_qpso_best = float("inf")

    local_search_count = 0

    for iteration in range(iterations):

        current_beta = _anneal_beta(beta, iteration, iterations)

        # Run one QPSO iteration.
        qpso.step(
            problem,
            fitness,
            beta=current_beta
        )

        current_qpso_best = qpso.global_best_fitness

        # Apply local search only when QPSO
        # discovers a new global best.
        if current_qpso_best < previous_qpso_best:

            if random.random() < local_search_probability:

                # Give local search several different starting points
                # (the top-K particles by personal-best fitness), not
                # just the single global best -- this is what lets the
                # hybrid escape a local optimum that one particle's
                # ordering happens to be stuck in.
                candidates = sorted(
                    qpso.particles,
                    key=lambda particle: particle.best_fitness
                )[:max(1, top_k_particles)]

                for particle in candidates:

                    decoded = _decode_particle(particle, problem)

                    if decoded is None:
                        continue

                    candidate_routes = decoded["routes"]
                    candidate_score = decoded["fitness"]

                    if candidate_score == float("inf"):
                        continue

                    improved_routes, improved_score = iterated_local_search(
                        candidate_routes,
                        problem,
                        fitness,
                        max_kicks=ils_max_kicks
                    )

                    local_search_count += 1

                    # Never allow local search to worsen the solution.
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
        num_particles=10,
        iterations=20,
        beta=0.5,
        local_search_probability=1.0
    )

    print("\n## Adaptive Hybrid QPSO + 2-opt Result")
    print("\nRoutes:", result["routes"])
    print("Fitness:", result["fitness"])
    print("Local search triggers:", result["local_search_count"])