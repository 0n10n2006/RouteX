import heapq


def dijkstra(graph, start, end):

    distances = {
        node: float("inf")
        for node in graph
    }

    distances[start] = 0

    previous = {
        node: None
        for node in graph
    }

    queue = []

    heapq.heappush(queue, (0, start))

    while queue:

        current_distance, current_node = heapq.heappop(queue)

        if current_distance > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node].items():

            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:

                distances[neighbor] = new_distance

                previous[neighbor] = current_node

                heapq.heappush(
                    queue,
                    (new_distance, neighbor)
                )

    if distances[end] == float("inf"):
        return [], float("inf")

    path = []

    current = end

    while current is not None:

        path.append(current)

        current = previous[current]

    path.reverse()

    return path, distances[end]

# Calculate total shortest-path distance for a VRP route
def calculate_route_distance(route, graph):
    total_distance = 0

    for i in range(len(route) - 1):

        start = route[i]
        end = route[i + 1]

        path, distance = dijkstra(graph, start, end)

        if not path:
            return float("inf")

        total_distance += distance

    return total_distance
