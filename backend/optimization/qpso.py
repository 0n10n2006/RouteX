
from qpso_utils import decode_random_keys, create_routes
from fitness import fitness
from problem import ProblemInstance

import random
class Particle:

    def __init__(self, position):
        self.position = position

        # Best position this particle has found
        self.best_position = position[:]

        # Fitness of current position
        self.fitness = float("inf")

        # Best fitness this particle has found
        self.best_fitness = float("inf")
    


class QPSO:

    def __init__(self, num_particles, num_customers):
        self.num_particles = num_particles
        self.num_customers = num_customers

        self.particles = []
        self.global_best_position = None
        self.global_best_fitness = float("inf")

        self.initialize_swarm()

    def initialize_swarm(self):

        for _ in range(self.num_particles):

            position = [
                random.random()
                for _ in range(self.num_customers)
            ]

            particle = Particle(position)

            self.particles.append(particle)
        
    def evaluate(self, problem, fitness_function):
        for particle in self.particles:

            customer_order = decode_random_keys(
                particle.position
            )

            routes = create_routes(
                customer_order,
                len(problem.vehicles)
            )

            score = fitness_function(
                routes,
                problem
            )["fitness"]

            particle.fitness = score

            # Update personal best
            if score < particle.best_fitness:
                particle.best_fitness = score
                particle.best_position = particle.position[:]

            # Update global best
            if score < self.global_best_fitness:
                self.global_best_fitness = score
                self.global_best_position = particle.position[:]

    def calculate_mbest(self):
        mbest = []

        for dimension in range(self.num_customers):

            average = sum(
                particle.best_position[dimension]
                for particle in self.particles
            ) / self.num_particles

            mbest.append(average)

        return mbest


if __name__ == "__main__":

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]

    problem = ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=[
            {"id": 1, "capacity": 10},
            {"id": 2, "capacity": 10}
        ],
        customers=[
            {"id": 1, "demand": 2},
            {"id": 2, "demand": 3},
            {"id": 3, "demand": 1},
            {"id": 4, "demand": 2}
        ]
    )

    qpso = QPSO(
        num_particles=5,
        num_customers=4
    )

    qpso.evaluate(problem, fitness)

    print("\nParticle results:")

    for i, particle in enumerate(qpso.particles):

        print(
            f"Particle {i + 1}:",
            particle.position,
            "Fitness:", particle.fitness,
            "Best:", particle.best_fitness
        )

    print("\nGlobal best fitness:", qpso.global_best_fitness)
    print("Global best position:", qpso.global_best_position)
    mbest = qpso.calculate_mbest()

    print("\nMbest:")
    print(mbest)