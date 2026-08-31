import csv
import time
from pathlib import Path

from backend.optimization.problem import ProblemInstance
from backend.optimization.greedy_vrp import greedy_vrp
from backend.optimization.fitness import fitness
from backend.optimization.constraints import validate
from backend.optimization.dijkstra import calculate_route_distance
from backend.optimization.ga import GeneticAlgorithm
from backend.optimization.pso import ParticleSwarmOptimization
from backend.optimization.qpso import QPSO
from backend.optimization.hybrid import hybrid_qpso

# --------------------------------------------------
# Create test problem
# --------------------------------------------------

def create_problem():

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]

    vehicles = [
        {"id": 1, "capacity": 10},
        {"id": 2, "capacity": 10}
    ]

    customers = [
        {"id": 1, "demand": 2},
        {"id": 2, "demand": 3},
        {"id": 3, "demand": 1},
        {"id": 4, "demand": 2}
    ]

    return ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )


# --------------------------------------------------
# Calculate total route distance
# --------------------------------------------------

def calculate_distance(routes, problem):

    total_distance = 0

    graph = {
        i: {
            j: problem.distance_matrix[i][j]
            for j in range(len(problem.distance_matrix))
            if i != j
        }
        for i in range(len(problem.distance_matrix))
    }

    for route in routes:

        distance = calculate_route_distance(
            route,
            graph
        )

        if distance == float("inf"):
            return float("inf")

        total_distance += distance

    return total_distance


# --------------------------------------------------
# Run one algorithm
# --------------------------------------------------

def run_algorithm(name, problem):

    start_time = time.perf_counter()

    routes = []
    best_fitness = float("inf")
    iterations = 0

    # ------------------------------
    # Greedy VRP
    # ------------------------------

    if name == "Greedy VRP":

        routes = greedy_vrp(problem)

        if routes and validate(routes, problem):
            best_fitness = fitness(routes, problem)

        iterations = 0

    # ------------------------------
    # Genetic Algorithm
    # ------------------------------

    elif name == "GA":

        algorithm = GeneticAlgorithm(
            population_size=20,
            generations=50,
            mutation_rate=0.1,
            crossover_rate=0.8
        )

        result = algorithm.solve(problem)

        if result is not None:
            routes = result["routes"]
            best_fitness = result["fitness"]

        iterations = algorithm.generations

    # ------------------------------
    # Particle Swarm Optimization
    # ------------------------------

    elif name == "PSO":

        algorithm = ParticleSwarmOptimization(
            num_particles=20,
            iterations=50,
            inertia=0.7,
            cognitive=1.5,
            social=1.5
        )

        result = algorithm.solve(problem)

        if result is not None:
            routes = result["routes"]
            best_fitness = result["fitness"]

        iterations = algorithm.iterations

    # ------------------------------
    # QPSO
    # ------------------------------

    elif name == "QPSO":

        algorithm = QPSO(
            num_particles=20,
            num_customers=len(problem.customers)
        )

        iterations = 50

        for _ in range(iterations):

            algorithm.step(
                problem,
                fitness,
                beta=0.5
            )

        result = algorithm.get_best_solution(problem)

        if result is not None:
            routes = result["routes"]
            best_fitness = result["fitness"]

    # ------------------------------
    # Hybrid QPSO
    # ------------------------------

    elif name == "Hybrid QPSO":

        result = hybrid_qpso(
            problem,
            num_particles=20,
            iterations=50,
            beta=0.5
        )

        if result is not None:
            routes = result["routes"]
            best_fitness = result["fitness"]

        iterations = 50

    runtime = time.perf_counter() - start_time

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    if routes and validate(routes, problem):

        constraint_violations = 0

        distance = calculate_distance(
            routes,
            problem
        )

    else:

        constraint_violations = 1
        distance = float("inf")

    return {
        "algorithm": name,
        "routes": routes,
        "fitness": best_fitness,
        "distance": distance,
        "runtime": runtime,
        "iterations": iterations,
        "constraint_violations": constraint_violations
    }


# --------------------------------------------------
# Main experiment
# --------------------------------------------------

def main():

    problem = create_problem()

    algorithms = [
        "Greedy VRP",
        "GA",
        "PSO",
        "QPSO",
        "Hybrid QPSO"
    ]

    results = []

    for algorithm in algorithms:

        print("\nRunning:", algorithm)

        result = run_algorithm(
            algorithm,
            problem
        )

        print("Routes:", result["routes"])
        print("Fitness:", result["fitness"])
        print("Distance:", result["distance"])
        print("Runtime:", result["runtime"])
        print("Iterations:", result["iterations"])
        print(
            "Constraint violations:",
            result["constraint_violations"]
        )

        results.append(result)

    # --------------------------------------------------
    # Save results
    # --------------------------------------------------

    output_file = Path(__file__).resolve().parent / "benchmark_results.csv"

    with open(
        output_file,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "algorithm",
            "fitness",
            "distance",
            "runtime",
            "iterations",
            "constraint_violations"
        ])

        for result in results:

            writer.writerow([
                result["algorithm"],
                result["fitness"],
                result["distance"],
                result["runtime"],
                result["iterations"],
                result["constraint_violations"]
            ])

    print("\n================================")
    print("Benchmark completed!")
    print("Results saved to benchmark_results.csv")
    print("================================")


if __name__ == "__main__":
    main()