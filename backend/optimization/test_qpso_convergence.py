import random

from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.problem import ProblemInstance


def create_problem():

    distance_matrix = [
        [0, 10, 15, 20, 8, 12, 18, 22, 14, 17, 25],
        [10, 0, 9, 12, 7, 11, 16, 20, 13, 15, 21],
        [15, 9, 0, 6, 11, 8, 14, 17, 10, 13, 19],
        [20, 12, 6, 0, 10, 9, 12, 15, 11, 14, 18],
        [8, 7, 11, 10, 0, 6, 13, 16, 9, 12, 17],
        [12, 11, 8, 9, 6, 0, 10, 14, 8, 11, 16],
        [18, 16, 14, 12, 13, 10, 0, 9, 11, 8, 14],
        [22, 20, 17, 15, 16, 14, 9, 0, 13, 10, 12],
        [14, 13, 10, 11, 9, 8, 11, 13, 0, 7, 15],
        [17, 15, 13, 14, 12, 11, 8, 10, 7, 0, 13],
        [25, 21, 19, 18, 17, 16, 14, 12, 15, 13, 0],
    ]

    customers = [
        {"id": i, "demand": 2}
        for i in range(1, 11)
    ]

    vehicles = [
        {"id": 1, "capacity": 15},
        {"id": 2, "capacity": 15},
        {"id": 3, "capacity": 15},
    ]

    return ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )


def find_convergence_iteration(history):
    """
    Return the first iteration where the final best fitness
    was reached and never improved afterwards.
    """

    final_value = history[-1]

    for i, value in enumerate(history):
        if value == final_value and all(
            later_value == final_value
            for later_value in history[i:]
        ):
            return i + 1

    return len(history)


def run_seed(seed, problem):

    random.seed(seed)

    qpso = QPSO(
        num_particles=20,
        num_customers=10
    )

    for _ in range(100):

        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

    convergence_iteration = find_convergence_iteration(
        qpso.convergence
    )

    return {
        "seed": seed,
        "final_fitness": qpso.global_best_fitness,
        "convergence_iteration": convergence_iteration,
        "history": qpso.convergence
    }


def main():

    problem = create_problem()

    seeds = range(1, 11)

    results = []

    print("=" * 70)
    print("QPSO MULTI-SEED CONVERGENCE TEST")
    print("=" * 70)

    for seed in seeds:

        result = run_seed(seed, problem)

        results.append(result)

        print(
            f"Seed {seed:2d} | "
            f"Final fitness: {result['final_fitness']:3d} | "
            f"Converged by iteration: "
            f"{result['convergence_iteration']:3d}"
        )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    convergence_iterations = [
        result["convergence_iteration"]
        for result in results
    ]

    final_fitnesses = [
        result["final_fitness"]
        for result in results
    ]

    average_convergence = (
        sum(convergence_iterations)
        / len(convergence_iterations)
    )

    print(
        f"Average convergence iteration: "
        f"{average_convergence:.2f}"
    )

    print(
        f"Earliest convergence: "
        f"{min(convergence_iterations)}"
    )

    print(
        f"Latest convergence: "
        f"{max(convergence_iterations)}"
    )

    print(
        f"Final fitness range: "
        f"{min(final_fitnesses)} - {max(final_fitnesses)}"
    )

    print("\nDetailed convergence histories:")

    for result in results:

        print(
            f"\nSeed {result['seed']} "
            f"(final = {result['final_fitness']}, "
            f"converged = iteration "
            f"{result['convergence_iteration']}):"
        )

        print(result["history"])


if __name__ == "__main__":
    main()