import random
import time

from .benchmark import (
    run_greedy,
    run_ga,
    run_pso,
    run_qpso,
    run_hybrid,
)
from .problem import ProblemInstance


# Same test problem for every algorithm
def create_problem(num_customers):
    size = num_customers + 1

    # Deterministic synthetic distance matrix
    random.seed(1000 + num_customers)

    matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            distance = random.randint(5, 100)
            matrix[i][j] = distance
            matrix[j][i] = distance

    # Two vehicles, enough capacity for the generated demands
    customers = [
        {
            "id": i,
            "demand": random.randint(1, 3),
        }
        for i in range(1, size)
    ]

    total_demand = sum(c["demand"] for c in customers)

    vehicles = [
        {
            "id": 1,
            "capacity": total_demand,
        },
        {
            "id": 2,
            "capacity": total_demand,
        },
    ]

    return ProblemInstance(
        distance_matrix=matrix,
        vehicles=vehicles,
        customers=customers,
    )


def run_algorithm(name, problem, seed):
    """
    Run one algorithm with the requested seed.

    The seed is reset immediately before each algorithm so every
    algorithm receives the same random-number starting state.
    """
    random.seed(seed)

    if name == "Greedy":
        return run_greedy(problem)

    if name == "GA":
        return run_ga(
            problem,
            population_size=20,
            generations=50,
        )

    if name == "PSO":
        return run_pso(
            problem,
            num_particles=20,
            iterations=50,
        )

    if name == "QPSO":
        return run_qpso(
            problem,
            num_particles=10,
            iterations=20,
            beta=0.5,
        )

    if name == "Hybrid QPSO + 2-opt":
        return run_hybrid(problem)

    raise ValueError(f"Unknown algorithm: {name}")


def main():
    algorithms = [
        "Greedy",
        "GA",
        "PSO",
        "QPSO",
        "Hybrid QPSO + 2-opt",
    ]

    seeds = [1, 2, 3, 4, 5]
    customer_sizes = [10, 20, 30]

    print("=" * 80)
    print("RouteX - ALL ALGORITHMS SANITY BENCHMARK")
    print("=" * 80)

    overall_results = {}

    for num_customers in customer_sizes:

        print(f"\n{'-' * 80}")
        print(f"{num_customers} CUSTOMERS")
        print(f"{'-' * 80}")

        problem = create_problem(num_customers)

        results = {
            algorithm: []
            for algorithm in algorithms
        }

        for seed in seeds:
            print(f"\nSeed {seed}")

            for algorithm in algorithms:

                result = run_algorithm(
                    algorithm,
                    problem,
                    seed,
                )

                results[algorithm].append(result)

                print(
                    f"{algorithm:<22} "
                    f"fitness={result['fitness']:8.2f} | "
                    f"time={result['runtime']:.4f}s"
                )

        print(f"\n{'SUMMARY':^80}")
        print("-" * 80)

        averages = {}

        for algorithm in algorithms:
            valid_results = [
                r for r in results[algorithm]
                if r["fitness"] != float("inf")
            ]

            if valid_results:
                avg_fitness = sum(
                    r["fitness"] for r in valid_results
                ) / len(valid_results)

                avg_runtime = sum(
                    r["runtime"] for r in valid_results
                ) / len(valid_results)

                feasible_count = len(valid_results)

            else:
                avg_fitness = float("inf")
                avg_runtime = float("inf")
                feasible_count = 0

            averages[algorithm] = avg_fitness

            print(
                f"{algorithm:<22} "
                f"avg fitness={avg_fitness:8.2f} | "
                f"avg time={avg_runtime:.4f}s | "
                f"feasible={feasible_count}/{len(seeds)}"
            )

        best_algorithm = min(
            averages,
            key=averages.get,
        )

        print("\nBEST:")
        print(
            f"  {best_algorithm} "
            f"(average fitness = {averages[best_algorithm]:.2f})"
        )

        overall_results[num_customers] = averages

    print("\n")
    print("=" * 80)
    print("FINAL WINNER BY PROBLEM SIZE")
    print("=" * 80)

    hybrid_wins = 0

    for num_customers, averages in overall_results.items():

        best_algorithm = min(
            averages,
            key=averages.get,
        )

        if best_algorithm == "Hybrid QPSO + 2-opt":
            hybrid_wins += 1

        print(
            f"{num_customers:2d} customers → "
            f"{best_algorithm} "
            f"({averages[best_algorithm]:.2f})"
        )

    print("\n")
    print(
        f"Hybrid QPSO + 2-opt wins "
        f"{hybrid_wins}/{len(customer_sizes)} problem sizes."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()