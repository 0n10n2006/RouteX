def route_distance(route, distance_matrix):
    total = 0

    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]

        total += distance_matrix[a][b]

    return total


def optimization_matrix(problem):
    """Return the matrix the algorithms should minimise.

    OSM-backed problems minimise simulated traffic-adjusted travel time.
    Older scenarios deliberately keep their established distance objective.
    """
    return problem.travel_time_matrix or problem.distance_matrix

# previous fitness function, commented out for reference
# def fitness(solution, problem):
#     total_distance = 0

#     for route in solution:
#         total_distance += route_distance(
#             route,
#             problem.distance_matrix
#         )

#     return {
#         "fitness": total_distance,
#         "distance": total_distance
#     }

def calculate_metrics(solution, problem):
    total_distance = 0

    for route in solution:
        total_distance += route_distance(
            route,
            problem.distance_matrix
        )

    metrics = {
        "distance": total_distance
    }

    if problem.travel_time_matrix is not None:
        metrics["travel_time"] = sum(
            route_distance(route, problem.travel_time_matrix)
            for route in solution
        )

    return metrics


def fitness(solution, problem):
    metrics = calculate_metrics(solution, problem)

    return metrics.get("travel_time", metrics["distance"])
