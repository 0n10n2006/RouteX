import random

from .qpso_utils import decode_random_keys, create_routes
from .fitness import fitness
from .constraints import validate


class Particle:

    def __init__(self, num_customers):
        self.position = [
            random.random()
            for _ in range(num_customers)
        ]

        self.velocity = [
            random.uniform(-0.1, 0.1)
            for _ in range(num_customers)
        ]

        self.best_position = self.position[:]
        self.fitness = float("inf")
        self.best_fitness = float("inf")

class ParticleSwarmOptimization:

    def __init__(
        self,
        num_particles=20,
        iterations=50,
        inertia=0.7,
        cognitive=1.5,
        social=1.5
    ):
        self.num_particles = num_particles
        self.iterations = iterations

        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social

        self.particles = []
        self.global_best_position = None
        self.global_best_fitness = float("inf")


    def initialize_swarm(self, num_customers):
        self.particles = []

        for _ in range(self.num_particles):
            particle = Particle(num_customers)
            self.particles.append(particle)

    def evaluate(self, problem):
        for particle in self.particles:

            customer_order = decode_random_keys(
                particle.position
            )

            routes = create_routes(
                customer_order,
                problem
            )

            if routes is None or not validate(routes, problem):
                score = float("inf")
            else:
                score = fitness(routes, problem)

            particle.fitness = score

            # Update personal best
            if score < particle.best_fitness:
                particle.best_fitness = score
                particle.best_position = particle.position[:]

            # Update global best
            if score < self.global_best_fitness:
                self.global_best_fitness = score
                self.global_best_position = particle.position[:]


    def update_velocity(self, particle):
        for i in range(len(particle.position)):

            r1 = random.random()
            r2 = random.random()

            cognitive = (
                self.cognitive
                * r1
                * (
                    particle.best_position[i]
                    - particle.position[i]
                )
            )

            social = (
                self.social
                * r2
                * (
                    self.global_best_position[i]
                    - particle.position[i]
                )
            )

            particle.velocity[i] = (
                self.inertia * particle.velocity[i]
                + cognitive
                + social
            )

    def update_position(self, particle):
        for i in range(len(particle.position)):

            particle.position[i] += particle.velocity[i]

            # Keep random key inside [0, 1]
            particle.position[i] = max(
                0.0,
                min(1.0, particle.position[i])
            )

    def solve(self, problem):
        self.initialize_swarm(
            len(problem.customers)
        )

        for _ in range(self.iterations):

            # Evaluate current particles
            self.evaluate(problem)

            # Move every particle
            for particle in self.particles:
                self.update_velocity(particle)
                self.update_position(particle)

        # Evaluate final positions
        self.evaluate(problem)

        if self.global_best_position is None:
            return None

        customer_order = decode_random_keys(
            self.global_best_position
        )

        routes = create_routes(
            customer_order,
            problem
        )

        return {
            "routes": routes,
            "fitness": self.global_best_fitness
        }