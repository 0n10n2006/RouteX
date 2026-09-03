import random
import time

from backend.optimization.problem import ProblemInstance
from backend.optimization.qpso import QPSO
from backend.optimization.hybrid import hybrid_qpso
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


def run_hybrid(problem, seed):
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

    print("\nWEEK 4 — FINAL QPSO vs ADAPTIVE HYBRID")
    print("=" * 75)

    for num_customers in [10, 20, 30]:

        print(f"\n--- {num_customers} CUSTOMERS ---")

        qpso_scores = []
        hybrid_scores = []

        qpso_times = []
        hybrid_times = []

        for seed in seeds:

            # Generate one identical problem for both algorithms.
            random.seed(42)

            problem = create_problem(
                num_customers
            )

            # -----------------------------
            # QPSO
            # -----------------------------

            qpso_result, qpso_time = run_qpso(
                problem,
                seed
            )

            qpso_score = qpso_result["fitness"]

            qpso_valid = validate(
                qpso_result["routes"],
                problem
            )

            # -----------------------------
            # Adaptive Hybrid QPSO + 2-opt
            # -----------------------------

            hybrid_result, hybrid_time = run_hybrid(
                problem,
                seed
            )

            hybrid_score = hybrid_result["fitness"]

            hybrid_valid = validate(
                hybrid_result["routes"],
                problem
            )

            # -----------------------------
            # Store results
            # -----------------------------

            qpso_scores.append(qpso_score)
            hybrid_scores.append(hybrid_score)

            qpso_times.append(qpso_time)
            hybrid_times.append(hybrid_time)

            improvement = (
                (qpso_score - hybrid_score)
                / qpso_score
                * 100
            )

            print(
                f"\nSeed {seed}:"
            )

            print(
                f"  QPSO:   "
                f"{qpso_score:.2f} | "
                f"time={qpso_time:.3f}s | "
                f"feasible={qpso_valid}"
            )

            print(
                f"  Hybrid: "
                f"{hybrid_score:.2f} | "
                f"time={hybrid_time:.3f}s | "
                f"improvement={improvement:.2f}% | "
                f"LS triggers="
                f"{hybrid_result['local_search_count']} | "
                f"feasible={hybrid_valid}"
            )

        # -----------------------------
        # Averages
        # -----------------------------

        avg_qpso = (
            sum(qpso_scores)
            / len(qpso_scores)
        )

        avg_hybrid = (
            sum(hybrid_scores)
            / len(hybrid_scores)
        )

        avg_qpso_time = (
            sum(qpso_times)
            / len(qpso_times)
        )

        avg_hybrid_time = (
            sum(hybrid_times)
            / len(hybrid_times)
        )

        avg_improvement = (
            (avg_qpso - avg_hybrid)
            / avg_qpso
            * 100
        )

        print("\n" + "-" * 75)

        print(
            f"SUMMARY {num_customers}: "
            f"QPSO avg={avg_qpso:.2f} | "
            f"Hybrid avg={avg_hybrid:.2f} | "
            f"improvement={avg_improvement:.2f}%"
        )

        print(
            f"Average runtime: "
            f"QPSO={avg_qpso_time:.3f}s | "
            f"Hybrid={avg_hybrid_time:.3f}s"
        )

    print("\n" + "=" * 75)
    print("FINAL WEEK 4 BENCHMARK COMPLETE")


if __name__ == "__main__":
    main()