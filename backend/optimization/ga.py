import random

from .qpso_utils import decode_random_keys, create_routes
from .fitness import fitness
from .constraints import validate


class GeneticAlgorithm:

    def __init__(
        self,
        population_size=20,
        generations=50,
        mutation_rate=0.1,
        crossover_rate=0.8
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

    def initialize_population(self, num_customers):
        population = []

        for _ in range(self.population_size):
            chromosome = [
                random.random()
                for _ in range(num_customers)
            ]

            population.append(chromosome)

        return population

    def evaluate_population(self, population, problem):
        evaluated = []

        for chromosome in population:

            customer_order = decode_random_keys(chromosome)

            routes = create_routes(
                customer_order,
                problem
            )

            if routes is None or not validate(routes, problem):
                score = float("inf")
            else:
                score = fitness(routes, problem)

            evaluated.append(
                {
                    "chromosome": chromosome,
                    "routes": routes,
                    "fitness": score
                }
            )

        return evaluated

    def tournament_selection(self, evaluated_population, tournament_size=3):
        tournament = random.sample(
            evaluated_population,
            tournament_size
        )

        winner = min(
            tournament,
            key=lambda individual: individual["fitness"]
        )

        return winner

    def crossover(self, parent1, parent2):
        if random.random() > self.crossover_rate:
            return parent1[:]

        point = random.randint(1, len(parent1) - 1)

        child = (
            parent1[:point]
            + parent2[point:]
        )

        return child

    def mutate(self, chromosome):
        for i in range(len(chromosome)):

            if random.random() < self.mutation_rate:
                chromosome[i] = random.random()

        return chromosome

    def create_next_generation(self, evaluated_population):
        evaluated_population.sort(
            key=lambda individual: individual["fitness"]
        )

        new_population = []

        # Keep the best individual
        new_population.append(
            evaluated_population[0]["chromosome"][:]
        )

        while len(new_population) < self.population_size:

            parent1 = self.tournament_selection(
                evaluated_population
            )

            parent2 = self.tournament_selection(
                evaluated_population
            )

            child = self.crossover(
                parent1["chromosome"],
                parent2["chromosome"]
            )

            child = self.mutate(child)

            new_population.append(child)

        return new_population

    def solve(self, problem):
        population = self.initialize_population(
            len(problem.customers)
        )

        best_solution = None
        best_fitness = float("inf")

        for _ in range(self.generations):

            evaluated_population = self.evaluate_population(
                population,
                problem
            )

            current_best = min(
                evaluated_population,
                key=lambda individual: individual["fitness"]
            )

            if current_best["fitness"] < best_fitness:
                best_fitness = current_best["fitness"]

                best_solution = {
                    "routes": current_best["routes"],
                    "fitness": current_best["fitness"]
                }

            population = self.create_next_generation(
                evaluated_population
            )

        return best_solution