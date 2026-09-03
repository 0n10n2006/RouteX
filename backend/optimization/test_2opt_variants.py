import random
import time

from backend.optimization.problem import ProblemInstance
from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.local_search import (
    two_opt,
    two_opt_first_improvement
)
from backend.optimization.constraints import validate


def create_problem(num_customers=20):
    size = num_customers + 1

    matrix = [[0 for _ in range(size)] for _ in range(size)]

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


def get_qpso_solution(problem, seed):
    random.seed(seed)

    qpso = QPSO(
        num_particles=20,
        num_customers=len(problem.customers)
    )

    for _ in range(100):
        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

    return qpso.get_best_solution(problem)


def main():

    seeds = [1, 2, 3, 4, 5]

    print("\nWEEK 4 — 2-OPT VARIANT TEST")
    print("=" * 80)

    for num_customers in [10, 20, 30]:

        print(f"\n--- {num_customers} CUSTOMERS ---")

        for seed in seeds:

            random.seed(42)
            problem = create_problem(num_customers)

            qpso_result = get_qpso_solution(
                problem,
                seed
            )

            qpso_score = qpso_result["fitness"]

            # Full 2-opt
            start = time.perf_counter()

            full_routes, full_score = two_opt(
                qpso_result["routes"],
                problem,
                fitness
            )

            full_time = time.perf_counter() - start

            # First-improvement 2-opt
            start = time.perf_counter()

            first_routes, first_score = two_opt_first_improvement(
                qpso_result["routes"],
                problem,
                fitness
            )

            first_time = time.perf_counter() - start

            full_improvement = (
                (qpso_score - full_score)
                / qpso_score
                * 100
            )

            first_improvement = (
                (qpso_score - first_score)
                / qpso_score
                * 100
            )

            full_valid = validate(
                full_routes,
                problem
            )

            first_valid = validate(
                first_routes,
                problem
            )

            print(
                f"Seed {seed}: "
                f"QPSO={qpso_score:.0f} | "
                f"Full={full_score:.0f} "
                f"({full_improvement:.2f}%, {full_time:.3f}s) | "
                f"First={first_score:.0f} "
                f"({first_improvement:.2f}%, {first_time:.3f}s) | "
                f"valid={full_valid}/{first_valid}"
            )

    print("\n" + "=" * 80)
    print("2-OPT VARIANT TEST COMPLETE")


if __name__ == "__main__":
    main()