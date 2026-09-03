import random
import time

from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.problem import ProblemInstance
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


def run_experiment(beta, seed, num_customers=20):
    random.seed(seed)

    problem = create_problem(num_customers)

    qpso = QPSO(
        num_particles=20,
        num_customers=num_customers
    )

    # Initial evaluation
    qpso.evaluate(problem, fitness)
    initial_fitness = qpso.global_best_fitness

    start = time.perf_counter()

    for _ in range(100):
        qpso.step(
            problem,
            fitness,
            beta=beta
        )

    runtime = time.perf_counter() - start

    final_fitness = qpso.global_best_fitness

    solution = qpso.get_best_solution(problem)

    feasible = (
        solution is not None
        and solution["routes"] is not None
        and validate(solution["routes"], problem)
    )

    improvement = (
        (initial_fitness - final_fitness)
        / initial_fitness
        * 100
    )

    return (
        initial_fitness,
        final_fitness,
        improvement,
        runtime,
        feasible
    )


def main():

    betas = [0.2, 0.3, 0.5, 0.7, 0.9]
    seeds = [1, 2, 3, 4, 5]

    print("\nQPSO BETA SENSITIVITY TEST")
    print("=" * 70)

    for beta in betas:

        results = []

        print(f"\n--- BETA = {beta} ---")

        for seed in seeds:

            result = run_experiment(
                beta=beta,
                seed=seed
            )

            results.append(result)

            initial, final, improvement, runtime, feasible = result

            print(
                f"Seed {seed}: "
                f"initial={initial:.2f} | "
                f"final={final:.2f} | "
                f"improvement={improvement:.2f}% | "
                f"time={runtime:.3f}s | "
                f"feasible={feasible}"
            )

        avg_final = sum(r[1] for r in results) / len(results)
        avg_improvement = sum(r[2] for r in results) / len(results)
        avg_runtime = sum(r[3] for r in results) / len(results)
        feasible_count = sum(r[4] for r in results)

        print(
            f"SUMMARY beta={beta}: "
            f"avg_final={avg_final:.2f} | "
            f"avg_improvement={avg_improvement:.2f}% | "
            f"avg_runtime={avg_runtime:.3f}s | "
            f"feasible={feasible_count}/{len(seeds)}"
        )

    print("\n" + "=" * 70)
    print("BETA SENSITIVITY COMPLETE")


if __name__ == "__main__":
    main()