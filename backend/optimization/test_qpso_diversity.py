import random

from backend.optimization.qpso import QPSO
from backend.optimization.fitness import fitness
from backend.optimization.problem import ProblemInstance
from backend.optimization.qpso_utils import decode_random_keys


def create_problem():

    random.seed(42)

    num_customers = 20

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
        {
            "id": i,
            "demand": 2
        }
        for i in range(1, num_customers + 1)
    ]

    vehicles = [
        {
            "id": i,
            "capacity": 20
        }
        for i in range(1, 6)
    ]

    return ProblemInstance(
        distance_matrix=matrix,
        vehicles=vehicles,
        customers=customers
    )


def route_signature(position):

    return tuple(
        decode_random_keys(position)
    )


def main():

    random.seed(42)

    problem = create_problem()

    qpso = QPSO(
        num_particles=20,
        num_customers=20
    )

    print("\nQPSO DIVERSITY TEST")
    print("=" * 60)

    for iteration in range(1, 101):

        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

        if iteration in [1, 5, 10, 20, 50, 100]:

            signatures = {
                route_signature(
                    particle.position
                )
                for particle in qpso.particles
            }

            print(
                f"Iteration {iteration:3d}: "
                f"unique routes = {len(signatures):2d} / "
                f"{len(qpso.particles)} | "
                f"best = {qpso.global_best_fitness}"
            )

    print("\nFinal particle routes:")

    for i, particle in enumerate(qpso.particles):

        route = decode_random_keys(
            particle.position
        )

        print(
            f"Particle {i + 1:2d}: {route}"
        )


if __name__ == "__main__":
    main()