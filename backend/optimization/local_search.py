def route_distance(route, distance_matrix):
    total = 0

    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]

        total += distance_matrix[a][b]

    return total


def two_opt(solution, problem, fitness_function):

    best_solution = [route[:] for route in solution]

    best_score = fitness_function(
        best_solution,
        problem
    )

    improved = True

    while improved:
        improved = False

        for route_index in range(len(best_solution)):

            route = best_solution[route_index]

            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route) - 1):

                    candidate_solution = [
                        r[:] for r in best_solution
                    ]

                    candidate_route = candidate_solution[route_index]

                    candidate_route[i:j + 1] = reversed(
                        candidate_route[i:j + 1]
                    )

                    candidate_score = fitness_function(
                        candidate_solution,
                        problem
                    )

                    if candidate_score < best_score:

                        best_solution = candidate_solution
                        best_score = candidate_score
                        improved = True

    return best_solution, best_score