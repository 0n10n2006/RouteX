import random

from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.problem import ProblemInstance


def main():

    random.seed(42)

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

    problem = ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )

    qpso = QPSO(
        num_particles=20,
        num_customers=10
    )

    for iteration in range(100):

        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

        if iteration == 0 or (iteration + 1) % 10 == 0:

            print(
                f"Iteration {iteration + 1:3d}: "
                f"{qpso.global_best_fitness}"
            )

    print("\nFinal fitness:")
    print(qpso.global_best_fitness)

    print("\nConvergence history:")
    print(qpso.convergence)


if __name__ == "__main__":
    main()