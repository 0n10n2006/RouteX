import random

from .benchmark import (
    run_greedy,
    run_ga,
    run_pso,
    run_qpso,
    run_hybrid,
)
from .traffic_scenarios import create_kothrud_problem


def run_algorithm(name, problem, seed):
    # Same starting random state for every algorithm
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

    print("=" * 80)
    print("RouteX - KOTHRUD ALL ALGORITHMS BENCHMARK")
    print("=" * 80)

    print("\nLoading Kothrud OSM + traffic scenario...")

    problem = create_kothrud_problem()

    print(f"Customers       : {len(problem.customers)}")
    print(f"Locations       : {len(problem.distance_matrix)}")
    print(f"Vehicles        : {len(problem.vehicles)}")
    print(
        f"Travel-time     : "
        f"{problem.travel_time_matrix is not None}"
    )

    results = {
        algorithm: []
        for algorithm in algorithms
    }

    print("\n" + "-" * 80)
    print("RUNS")
    print("-" * 80)

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
                f"fitness={result['fitness']:10.4f} | "
                f"time={result['runtime']:.4f}s | "
                f"feasible="
                f"{result['fitness'] != float('inf')}"
            )

    print("\n")
    print("=" * 80)
    print("KOTHRUD SUMMARY")
    print("=" * 80)

    averages = {}

    for algorithm in algorithms:

        valid_results = [
            result
            for result in results[algorithm]
            if result["fitness"] != float("inf")
        ]

        if not valid_results:
            averages[algorithm] = float("inf")

            print(
                f"{algorithm:<22} "
                f"NO FEASIBLE RESULTS"
            )

            continue

        avg_fitness = sum(
            result["fitness"]
            for result in valid_results
        ) / len(valid_results)

        avg_runtime = sum(
            result["runtime"]
            for result in valid_results
        ) / len(valid_results)

        averages[algorithm] = avg_fitness

        print(
            f"{algorithm:<22} "
            f"avg fitness={avg_fitness:10.4f} | "
            f"avg time={avg_runtime:.4f}s | "
            f"feasible="
            f"{len(valid_results)}/{len(seeds)}"
        )

    best_algorithm = min(
        averages,
        key=averages.get,
    )

    print("\n" + "-" * 80)
    print("WINNER")
    print("-" * 80)

    print(
        f"Best average fitness : "
        f"{best_algorithm}"
    )

    print(
        f"Average fitness      : "
        f"{averages[best_algorithm]:.4f}"
    )

    # Explicit Hybrid check
    hybrid_avg = averages["Hybrid QPSO + 2-opt"]

    print("\nHybrid QPSO + 2-opt check:")

    if best_algorithm == "Hybrid QPSO + 2-opt":
        print(
            "✓ Hybrid has the best average fitness "
            "among all five algorithms."
        )
    else:
        print(
            "⚠ Hybrid is NOT the best average performer "
            "in this Kothrud test."
        )

    # Count individual seed wins
    hybrid_wins = 0

    for i, seed in enumerate(seeds):

        seed_values = {
            algorithm: results[algorithm][i]["fitness"]
            for algorithm in algorithms
        }

        seed_best = min(
            seed_values,
            key=seed_values.get,
        )

        if seed_best == "Hybrid QPSO + 2-opt":
            hybrid_wins += 1

    print(
        f"Hybrid individual-seed wins: "
        f"{hybrid_wins}/{len(seeds)}"
    )

    print("\n" + "=" * 80)
    print("KOTHRUD BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
