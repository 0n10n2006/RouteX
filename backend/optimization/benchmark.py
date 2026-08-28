import time

from qpso import QPSO
from problem import ProblemInstance
from greedy_vrp import greedy_vrp
from fitness import fitness
from constraints import validate
from hybrid import hybrid_qpso
from dijkstra import calculate_route_distance

def run_hybrid(problem):

    start_time = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=10,
        iterations=20,
        beta=0.5
    )

    runtime = time.perf_counter() - start_time

    if result is None or not validate(result["routes"], problem):
        return {
            "algorithm": "Hybrid QPSO + 2-opt",
            "routes": [],
            "fitness": float("inf"),
            "runtime": runtime
        }

    return {
        "algorithm": "Hybrid QPSO + 2-opt",
        "routes": result["routes"],
        "fitness": result["fitness"],
        "runtime": runtime
    }

def run_greedy(problem):

    start_time = time.perf_counter()

    routes = greedy_vrp(problem)

    runtime = time.perf_counter() - start_time

    if not routes or not validate(routes, problem):
        return {
            "algorithm": "Greedy VRP",
            "routes": routes,
            "fitness": float("inf"),
            "runtime": runtime
        }

    score = fitness(routes, problem)

    return {
        "algorithm": "Greedy VRP",
        "routes": routes,
        "fitness": score,
        "runtime": runtime
    }

def run_qpso(problem, num_particles=10, iterations=20, beta=0.5):

    start_time = time.perf_counter()

    qpso = QPSO(
        num_particles=num_particles,
        num_customers=len(problem.customers)
    )

    for _ in range(iterations):
        qpso.step(
            problem,
            fitness,
            beta=beta
        )

    result = qpso.get_best_solution(problem)

    runtime = time.perf_counter() - start_time

    if result is None or not validate(result["routes"], problem):
        return {
            "algorithm": "QPSO",
            "routes": [],
            "fitness": float("inf"),
            "runtime": runtime
        }

    return {
        "algorithm": "QPSO",
        "routes": result["routes"],
        "fitness": result["fitness"],
        "runtime": runtime
    }
def evaluate_routes_with_dijkstra(routes, problem):

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

    result = run_greedy(problem)
    

    print("\nGreedy VRP Result")
    print("-----------------")
    print("Routes:", result["routes"])
    print("Fitness:", result["fitness"])
    print("Runtime:", result["runtime"])

    qpso_result = run_qpso(problem)

    print("\nQPSO Result")
    print("-----------")
    print("Routes:", qpso_result["routes"])
    print("Fitness:", qpso_result["fitness"])
    print("Runtime:", qpso_result["runtime"])

    hybrid_result = run_hybrid(problem)

    print("\nHybrid QPSO + 2-opt Result")
    print("--------------------------")
    print("Routes:", hybrid_result["routes"])
    print("Fitness:", hybrid_result["fitness"])
    print("Runtime:", hybrid_result["runtime"])
    
    greedy_routes = greedy_vrp(problem)

    dijkstra_distance = evaluate_routes_with_dijkstra(
        greedy_routes,
        problem
    )

    print("\nDijkstra evaluation of Greedy routes:")
    print("Distance:", dijkstra_distance)