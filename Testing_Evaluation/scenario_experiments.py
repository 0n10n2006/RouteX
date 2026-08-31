import csv
import time
import random
import math
from pathlib import Path

from backend.optimization.problem import ProblemInstance
from backend.optimization.greedy_vrp import greedy_vrp
from backend.optimization.fitness import fitness
from backend.optimization.constraints import validate
from backend.optimization.ga import GeneticAlgorithm
from backend.optimization.pso import ParticleSwarmOptimization
from backend.optimization.qpso import QPSO
from backend.optimization.hybrid import hybrid_qpso

from Testing_Evaluation.traffic_model import get_traffic_factor

scenarios = [
{
"id": "S1",
"demand": "Low",
"traffic": "Low",
"incident": False,
"vehicles": 3,
"delivery_points": 10
},
{
"id": "S2",
"demand": "Medium",
"traffic": "Medium",
"incident": False,
"vehicles": 5,
"delivery_points": 15
},
{
"id": "S3",
"demand": "High",
"traffic": "High",
"incident": False,
"vehicles": 10,
"delivery_points": 25
},
{
"id": "S4",
"demand": "Medium",
"traffic": "High",
"incident": True,
"vehicles": 5,
"delivery_points": 15
},
{
"id": "S5",
"demand": "High",
"traffic": "High",
"incident": True,
"vehicles": 10,
"delivery_points": 25
}
]
def create_distance_matrix(num_points, traffic, incident, seed):
    random.seed(seed)

    coordinates = []

    for _ in range(num_points):
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        coordinates.append((x, y))

    factor = get_traffic_factor(traffic)

    matrix = []

    for i in range(num_points):
        row = []

        for j in range(num_points):
            if i == j:
                row.append(0)
                continue

            x1, y1 = coordinates[i]
            x2, y2 = coordinates[j]

            distance = math.sqrt(
                (x1 - x2) ** 2 +
                (y1 - y2) ** 2
            )

            distance *= factor

            if incident and (i + j) % 5 == 0:
                distance *= 1.8

            row.append(round(distance, 2))

        matrix.append(row)

    return matrix

def create_problem(scenario):
    num_customers = scenario["delivery_points"]

    distance_matrix = create_distance_matrix(
        num_customers + 1,
        scenario["traffic"],
        scenario["incident"],
        seed=100 + num_customers
    )

    demand_range = {
        "Low": (1, 2),
        "Medium": (2, 4),
        "High": (3, 6)
    }

    low, high = demand_range[scenario["demand"]]

    customers = []

    random.seed(200 + num_customers)

    for customer_id in range(1, num_customers + 1):
        customers.append({
            "id": customer_id,
            "demand": random.randint(low, high)
        })

    if scenario["demand"] == "Low":
        capacity = 15
    elif scenario["demand"] == "Medium":
        capacity = 20
    else:
        capacity = 25

    vehicles = []

    for vehicle_id in range(1, scenario["vehicles"] + 1):
        vehicles.append({
            "id": vehicle_id,
            "capacity": capacity
        })

    return ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )


def run_algorithm(name, problem):
    start_time = time.perf_counter()

    routes = None
    best_fitness = float("inf")
    iterations = 0

    if name == "Greedy VRP":
        routes = greedy_vrp(problem)

        if routes and validate(routes, problem):
            best_fitness = fitness(routes, problem)

        iterations = 0

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

        iterations = 50

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

        iterations = 50

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

    if routes and validate(routes, problem):
        constraint_violations = 0
        distance = fitness(routes, problem)
    else:
        constraint_violations = 1
        distance = float("inf")

    return {
        "routes": routes,
        "fitness": best_fitness,
        "distance": distance,
        "runtime": runtime,
        "iterations": iterations,
        "constraint_violations": constraint_violations
    }

def main():
    algorithms = [
        "Greedy VRP",
        "GA",
        "PSO",
        "QPSO",
        "Hybrid QPSO"
    ]

    results = []

    for scenario in scenarios:
        print()
        print("==============================================")
        print("Scenario:", scenario["id"])
        print("Demand:", scenario["demand"])
        print("Traffic:", scenario["traffic"])
        print("Incident:", scenario["incident"])
        print("Vehicles:", scenario["vehicles"])
        print("Delivery Points:", scenario["delivery_points"])
        print("==============================================")

        problem = create_problem(scenario)

        for algorithm_name in algorithms:
            random.seed(1000 + len(results))

            print()
            print("Running:", algorithm_name)

            result = run_algorithm(
                algorithm_name,
                problem
            )

            print("Fitness:", result["fitness"])
            print("Distance:", result["distance"])
            print("Runtime:", result["runtime"])
            print("Iterations:", result["iterations"])
            print(
                "Constraint violations:",
                result["constraint_violations"]
            )

            results.append({
                "scenario_id": scenario["id"],
                "demand": scenario["demand"],
                "traffic": scenario["traffic"],
                "incident": scenario["incident"],
                "vehicles": scenario["vehicles"],
                "delivery_points": scenario["delivery_points"],
                "algorithm": algorithm_name,
                "fitness": result["fitness"],
                "distance": result["distance"],
                "runtime": result["runtime"],
                "iterations": result["iterations"],
                "constraint_violations": result["constraint_violations"]
            })

    output_file = (
        Path(__file__).resolve().parent
        / "scenario_benchmark_results.csv"
    )

    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "scenario_id",
                "demand",
                "traffic",
                "incident",
                "vehicles",
                "delivery_points",
                "algorithm",
                "fitness",
                "distance",
                "runtime",
                "iterations",
                "constraint_violations"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print()
    print("==============================================")
    print("SCENARIO BENCHMARK COMPLETED!")
    print("==============================================")
    print("Results saved to:", output_file)


if __name__ == "__main__":
    main()