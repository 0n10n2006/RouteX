def route_distance(route, distance_matrix):
    total = 0

    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]

        total += distance_matrix[a][b]

    return total


def fitness(solution, problem):
    total_distance = 0

    for route in solution:
        total_distance += route_distance(
            route,
            problem.distance_matrix
        )

    return {
        "fitness": total_distance,
        "distance": total_distance
    }
