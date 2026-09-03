from .qpso_utils import decode_random_keys
from .repair import repair_solution
from .problem import ProblemInstance
from .constraints import validate

import math
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

        # Store best fitness after every iteration
        self.convergence = []

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

            # Convert QPSO position → customer order
            customer_order = decode_random_keys(
                particle.position
            )

            # Convert customer order → vehicle routes
            routes = repair_solution(
                customer_order,
                problem
            )

            if routes is None:

                particle.fitness = float("inf")
                continue

            # Validate solution
            if not validate(routes, problem):

                score = float("inf")

            else:

                score = fitness_function(
                    routes,
                    problem
                )

            particle.fitness = score

            # Update personal best
            if score < particle.best_fitness:

                particle.best_fitness = score

                particle.best_position = (
                    particle.position[:]
                )

            # Update global best
            if score < self.global_best_fitness:

                self.global_best_fitness = score

                self.global_best_position = (
                    particle.position[:]
                )

    def calculate_mbest(self):

        mbest = []

        for dimension in range(self.num_customers):

            average = sum(
                particle.best_position[dimension]
                for particle in self.particles
            ) / self.num_particles

            mbest.append(average)

        return mbest

    def calculate_attractor(self, particle):

        attractor = []

        for i in range(self.num_customers):

            phi = random.random()

            value = (
                phi * particle.best_position[i]
                + (1 - phi) * self.global_best_position[i]
            )

            attractor.append(value)

        return attractor

    def update_particle(
        self,
        particle,
        mbest,
        beta=0.5
    ):

        attractor = self.calculate_attractor(
            particle
        )

        new_position = []

        for i in range(self.num_customers):

            # Random number for QPSO update
            u = random.random()

            # Avoid log(0)
            u = max(u, 1e-10)

            distance = abs(
                mbest[i] - particle.position[i]
            )

            step = (
                beta
                * distance
                * math.log(1 / u)
            )

            # Randomly choose direction
            if random.random() < 0.5:

                new_value = (
                    attractor[i] + step
                )

            else:

                new_value = (
                    attractor[i] - step
                )

            # Keep random key inside [0, 1]
            new_value = max(
                0.0,
                min(1.0, new_value)
            )

            new_position.append(new_value)

        particle.position = new_position

    def step(
        self,
        problem,
        fitness_function,
        beta=0.5
    ):

        # Evaluate current particles
        self.evaluate(
            problem,
            fitness_function
        )

        # Calculate mean best position
        mbest = self.calculate_mbest()

        # Move particles
        for particle in self.particles:

            self.update_particle(
                particle,
                mbest,
                beta
            )

        # Evaluate new positions
        self.evaluate(
            problem,
            fitness_function
        )

        self.convergence.append(
            self.global_best_fitness
        )

    def get_best_solution(self, problem):

        if self.global_best_position is None:
            return None

        customer_order = decode_random_keys(
            self.global_best_position
        )

        routes = repair_solution(
            customer_order,
            problem
        )

        return {
            "routes": routes,
            "fitness": self.global_best_fitness
        }


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

    print("QPSO convergence:\n")

    for iteration in range(20):

        qpso.step(
            problem,
            lambda solution, problem: sum(
                sum(
                    problem.distance_matrix[
                        route[i]
                    ][
                        route[i + 1]
                    ]
                    for i in range(len(route) - 1)
                )
                for route in solution
            ),
            beta=0.5
        )

        print(
            f"Iteration {iteration + 1}: "
            f"{qpso.global_best_fitness}"
        )

    print("\nFinal global best:")
    print(qpso.global_best_fitness)

    print("\nBest position:")
    print(qpso.global_best_position)

    print("\nConvergence:")
    print(qpso.convergence)