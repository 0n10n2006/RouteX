
import random
import time
import statistics

from backend.optimization.problem import ProblemInstance
from backend.optimization.qpso import QPSO
from backend.optimization.hybrid import hybrid_qpso
from backend.optimization.local_search import two_opt
from backend.optimization.fitness import fitness
from backend.optimization.constraints import validate


def create_problem(num_customers=20):
    size = num_customers + 1

    matrix = [
        [0 for _ in range(size)]
        for _ in range(size)
    ]

    for i in range(size):
        for j in range(i + 1, size):
            distance = random.randint(5, 50)
            matrix[i][j] = distance
            matrix[j][i] = distance

    customers = [
        {"id": i, "demand": 2}
        for i in range(1, num_customers + 1)
    ]

    vehicles = [
        {"id": i, "capacity": 20}
        for i in range(1, 6)
    ]

    return ProblemInstance(
        distance_matrix=matrix,
        vehicles=vehicles,
        customers=customers
    )


def run_qpso(problem, seed):
    random.seed(seed)

    qpso = QPSO(
        num_particles=20,
        num_customers=len(problem.customers)
    )

    start = time.perf_counter()

    for _ in range(100):
        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

    runtime = time.perf_counter() - start

    result = qpso.get_best_solution(problem)

    return result, runtime


def run_qpso_2opt(problem, seed):
    """
    QPSO + 2-opt without feedback injection.

    This isolates the contribution of local search.
    """

    random.seed(seed)

    qpso = QPSO(
        num_particles=20,
        num_customers=len(problem.customers)
    )

    best_routes = None
    best_score = float("inf")

    local_search_count = 0

    start = time.perf_counter()

    previous_qpso_best = float("inf")

    for _ in range(100):

        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

        current_qpso_best = qpso.global_best_fitness

        # Trigger 2-opt whenever QPSO finds a new global best.
        if current_qpso_best < previous_qpso_best:

            result = qpso.get_best_solution(problem)

            if result is not None:

                candidate_routes = result["routes"]
                candidate_score = result["fitness"]

                improved_routes, improved_score = two_opt(
                    candidate_routes,
                    problem,
                    fitness
                )

                local_search_count += 1

                # Never allow local search to worsen the solution.
                if improved_score > candidate_score:
                    improved_routes = candidate_routes
                    improved_score = candidate_score

                if improved_score < best_score:

                    best_routes = [
                        route[:]
                        for route in improved_routes
                    ]

                    best_score = improved_score

            previous_qpso_best = current_qpso_best

    runtime = time.perf_counter() - start

    if best_routes is None:

        result = qpso.get_best_solution(problem)

        if result is None:
            return None, runtime, local_search_count

        best_routes = result["routes"]
        best_score = result["fitness"]

    return {
        "algorithm": "QPSO + 2-opt",
        "routes": best_routes,
        "fitness": best_score
    }, runtime, local_search_count


def run_adaptive_hybrid(problem, seed):
    """
    Adaptive Hybrid QPSO + 2-opt.

    The current hybrid implementation does NOT use
    feedback injection. It returns local_search_count.
    """

    random.seed(seed)

    start = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=20,
        iterations=100,
        beta=0.5
    )

    runtime = time.perf_counter() - start

    return result, runtime


def main():

    seeds = [1, 2, 3, 4, 5]

    print("\nWEEK 4 — THREE-WAY ABLATION")
    print("=" * 80)

    for num_customers in [10, 20, 30]:

        print(f"\n--- {num_customers} CUSTOMERS ---")

        qpso_scores = []
        local_search_scores = []
        hybrid_scores = []

        qpso_times = []
        local_search_times = []
        hybrid_times = []

        hybrid_local_search_counts = []
        local_search_counts = []

        for seed in seeds:

            # --------------------------------------------------
            # Same problem for all three algorithms
            # --------------------------------------------------

            random.seed(42)

            problem = create_problem(
                num_customers
            )

            # --------------------------------------------------
            # 1. QPSO
            # --------------------------------------------------

            qpso_result, qpso_time = run_qpso(
                problem,
                seed
            )

            qpso_score = qpso_result["fitness"]

            qpso_valid = validate(
                qpso_result["routes"],
                problem
            )

            # --------------------------------------------------
            # 2. QPSO + 2-opt
            # --------------------------------------------------

            local_result, local_time, ls_count = run_qpso_2opt(
                problem,
                seed
            )

            local_score = local_result["fitness"]

            local_valid = validate(
                local_result["routes"],
                problem
            )

            # --------------------------------------------------
            # 3. Adaptive Hybrid QPSO + 2-opt
            # --------------------------------------------------

            hybrid_result, hybrid_time = run_adaptive_hybrid(
                problem,
                seed
            )

            hybrid_score = hybrid_result["fitness"]

            hybrid_valid = validate(
                hybrid_result["routes"],
                problem
            )

            # Current hybrid.py returns local_search_count.
            hybrid_ls_count = hybrid_result.get(
                "local_search_count",
                0
            )

            # --------------------------------------------------
            # Store results
            # --------------------------------------------------

            qpso_scores.append(qpso_score)
            local_search_scores.append(local_score)
            hybrid_scores.append(hybrid_score)

            qpso_times.append(qpso_time)
            local_search_times.append(local_time)
            hybrid_times.append(hybrid_time)

            hybrid_local_search_counts.append(
                hybrid_ls_count
            )

            local_search_counts.append(
                ls_count
            )

            # --------------------------------------------------
            # Improvements relative to QPSO
            # --------------------------------------------------

            local_improvement = (
                (qpso_score - local_score)
                / qpso_score
                * 100
            )

            hybrid_improvement = (
                (qpso_score - hybrid_score)
                / qpso_score
                * 100
            )

            # Additional benefit of hybrid over plain 2-opt
            hybrid_gain = (
                (local_score - hybrid_score)
                / local_score
                * 100
            )

            print(
                f"\nSeed {seed}:"
            )

            print(
                f"  QPSO:                  "
                f"{qpso_score:.2f} | "
                f"{qpso_time:.3f}s | "
                f"feasible={qpso_valid}"
            )

            print(
                f"  QPSO + 2-opt:          "
                f"{local_score:.2f} | "
                f"{local_time:.3f}s | "
                f"improvement={local_improvement:.2f}% | "
                f"LS triggers={ls_count} | "
                f"feasible={local_valid}"
            )

            print(
                f"  Adaptive Hybrid:       "
                f"{hybrid_score:.2f} | "
                f"{hybrid_time:.3f}s | "
                f"improvement={hybrid_improvement:.2f}% | "
                f"LS triggers={hybrid_ls_count} | "
                f"feasible={hybrid_valid}"
            )

            print(
                f"  Hybrid gain over "
                f"2-opt: {hybrid_gain:.2f}%"
            )

        # ------------------------------------------------------
        # Averages
        # ------------------------------------------------------

        avg_qpso = (
            sum(qpso_scores)
            / len(qpso_scores)
        )

        avg_local = (
            sum(local_search_scores)
            / len(local_search_scores)
        )

        avg_hybrid = (
            sum(hybrid_scores)
            / len(hybrid_scores)
        )

        avg_qpso_time = (
            sum(qpso_times)
            / len(qpso_times)
        )

        avg_local_time = (
            sum(local_search_times)
            / len(local_search_times)
        )

        avg_hybrid_time = (
            sum(hybrid_times)
            / len(hybrid_times)
        )

        # ------------------------------------------------------
        # Standard deviations
        # ------------------------------------------------------

        std_qpso = statistics.stdev(qpso_scores)
        std_local = statistics.stdev(local_search_scores)
        std_hybrid = statistics.stdev(hybrid_scores)

        # ------------------------------------------------------
        # Average local-search triggers
        # ------------------------------------------------------

        avg_local_triggers = (
            sum(local_search_counts)
            / len(local_search_counts)
        )

        avg_hybrid_triggers = (
            sum(hybrid_local_search_counts)
            / len(hybrid_local_search_counts)
        )

        # ------------------------------------------------------
        # Improvements
        # ------------------------------------------------------

        local_improvement = (
            (avg_qpso - avg_local)
            / avg_qpso
            * 100
        )

        hybrid_improvement = (
            (avg_qpso - avg_hybrid)
            / avg_qpso
            * 100
        )

        hybrid_gain = (
            (avg_local - avg_hybrid)
            / avg_local
            * 100
        )

        # ------------------------------------------------------
        # Summary
        # ------------------------------------------------------

        print("\n" + "-" * 80)

        print(
            f"SUMMARY {num_customers} CUSTOMERS"
        )

        print(
            f"QPSO avg:                  "
            f"{avg_qpso:.2f}"
        )

        print(
            f"QPSO + 2-opt avg:          "
            f"{avg_local:.2f}"
        )

        print(
            f"Adaptive Hybrid avg:       "
            f"{avg_hybrid:.2f}"
        )

        print(
            f"\nQPSO consistency (SD):       "
            f"{std_qpso:.2f}"
        )

        print(
            f"QPSO + 2-opt consistency:    "
            f"{std_local:.2f}"
        )

        print(
            f"Adaptive Hybrid consistency: "
            f"{std_hybrid:.2f}"
        )

        print(
            f"\n2-opt improvement:            "
            f"{local_improvement:.2f}%"
        )

        print(
            f"Hybrid improvement:           "
            f"{hybrid_improvement:.2f}%"
        )

        print(
            f"Hybrid gain over 2-opt:       "
            f"{hybrid_gain:.2f}%"
        )

        print(
            f"\nAvg QPSO + 2-opt LS triggers: "
            f"{avg_local_triggers:.2f}"
        )

        print(
            f"Avg Hybrid LS triggers:       "
            f"{avg_hybrid_triggers:.2f}"
        )

        print(
            f"\nAvg QPSO time:                "
            f"{avg_qpso_time:.3f}s"
        )

        print(
            f"Avg QPSO + 2-opt time:        "
            f"{avg_local_time:.3f}s"
        )

        print(
            f"Avg Adaptive Hybrid time:     "
            f"{avg_hybrid_time:.3f}s"
        )

    print("\n" + "=" * 80)
    print("WEEK 4 THREE-WAY ABLATION COMPLETE")


if __name__ == "__main__":
    main()

