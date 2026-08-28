def greedy_vrp(problem):

    unvisited = {
        customer["id"]
        for customer in problem.customers
    }

    routes = []

    for vehicle in problem.vehicles:

        route = [0]
        current_node = 0
        current_load = 0

        while unvisited:

            nearest_customer = None
            nearest_distance = float("inf")
            selected_demand = 0

            for customer_id in unvisited:

                for customer in problem.customers:

                    if customer["id"] == customer_id:
                        demand = customer["demand"]
                        break

                if current_load + demand > vehicle["capacity"]:
                    continue

                distance = (
                    problem.distance_matrix[current_node][customer_id]
                )

                if distance < nearest_distance:

                    nearest_distance = distance
                    nearest_customer = customer_id
                    selected_demand = demand

            if nearest_customer is None:
                break

            route.append(nearest_customer)

            current_load += selected_demand
            current_node = nearest_customer

            unvisited.remove(nearest_customer)

        route.append(0)

        if len(route) > 2:
            routes.append(route)

    return routes