import random
import time
import statistics

from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.constraints import validate
from backend.optimization.problem import ProblemInstance


def create_problem(num_customers, seed):
    """
    Create a reproducible synthetic CVRP instance.
    """

    random.seed(seed)

    # Depot is node 0.
    size = num_customers + 1

    # Symmetric distance matrix.
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for i in range(size):
        for j in range(i + 1, size):
            distance = random.randint(5, 50)

            matrix[i][j] = distance
            matrix[j][i] = distance

    customers = []

    for i in range(1, num_customers + 1):
        customers.append({
            "id": i,
            "demand": random.randint(1, 5)
        })

    # Keep the instance comfortably feasible.
    vehicles = [
        {"id": 1, "capacity": 30},
        {"id": 2, "capacity": 30},
        {"id": 3, "capacity": 30},
        {"id": 4, "capacity": 30},
        {"id": 5, "capacity": 30},
    ]

    return ProblemInstance(
        distance_matrix=matrix,
        vehicles=vehicles,
        customers=customers
    )


def run_single(num_customers, seed):

    random.seed(seed)

    problem = create_problem(
        num_customers,
        seed
    )

    qpso = QPSO(
        num_particles=20,
        num_customers=num_customers
    )

    start = time.perf_counter()

    # Initial evaluation.
    qpso.evaluate(
        problem,
        fitness
    )

    initial_fitness = qpso.global_best_fitness

    # Run 100 QPSO iterations.
    for _ in range(100):
        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

    elapsed = time.perf_counter() - start

    result = qpso.get_best_solution(problem)

    routes = result["routes"]
    final_fitness = result["fitness"]

    feasible = validate(
        routes,
        problem
    )

    improvement = (
        (initial_fitness - final_fitness)
        / initial_fitness
        * 100
    )

    return {
        "customers": num_customers,
        "seed": seed,
        "initial": initial_fitness,
        "final": final_fitness,
        "improvement": improvement,
        "runtime": elapsed,
        "feasible": feasible,
        "routes": routes,
        "convergence": qpso.convergence,
    }


def main():

    problem_sizes = [
        5,
        10,
        15,
        20,
        30
    ]

    seeds = [
        1,
        2,
        3,
        4,
        5
    ]

    print()
    print("=" * 70)
    print("QPSO WEEK 3 BASELINE")
    print("=" * 70)

    for size in problem_sizes:

        print()
        print(f"--- {size} CUSTOMERS ---")

        results = []

        for seed in seeds:

            try:

                result = run_single(
                    size,
                    seed
                )

                results.append(result)

                print(
                    f"Seed {seed}: "
                    f"initial={result['initial']:.2f} | "
                    f"final={result['final']:.2f} | "
                    f"improvement={result['improvement']:.2f}% | "
                    f"time={result['runtime']:.3f}s | "
                    f"feasible={result['feasible']}"
                )

            except Exception as error:

                print(
                    f"Seed {seed}: FAILED -> "
                    f"{type(error).__name__}: {error}"
                )

        if results:

            values = [
                result["final"]
                for result in results
            ]

            improvements = [
                result["improvement"]
                for result in results
            ]

            runtimes = [
                result["runtime"]
                for result in results
            ]

            print()
            print(
                f"SUMMARY {size}: "
                f"mean={statistics.mean(values):.2f} | "
                f"best={min(values):.2f} | "
                f"worst={max(values):.2f} | "
                f"std={statistics.stdev(values):.2f}"
            )

            print(
                f"Average improvement: "
                f"{statistics.mean(improvements):.2f}%"
            )

            print(
                f"Average runtime: "
                f"{statistics.mean(runtimes):.3f}s"
            )

    print()
    print("=" * 70)
    print("QPSO BASELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()