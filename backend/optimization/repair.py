def repair_solution(customer_order, problem):
    """
    Convert a customer order into feasible vehicle routes
    while respecting vehicle capacities.
    """

    # One route slot for each vehicle
    routes = [
        [0]
        for _ in problem.vehicles
    ]

    remaining_capacity = [
        vehicle["capacity"]
        for vehicle in problem.vehicles
    ]

    for customer_id in customer_order:

        # Find customer demand
        demand = None

        for customer in problem.customers:
            if customer["id"] == customer_id:
                demand = customer["demand"]
                break

        # Unknown customer
        if demand is None:
            return None

        # Customer cannot fit in any vehicle
        if demand > max(remaining_capacity):
            return None

        # Find best vehicle
        best_vehicle = None
        best_remaining = float("inf")

        for i in range(len(problem.vehicles)):

            if remaining_capacity[i] >= demand:

                leftover = remaining_capacity[i] - demand

                if leftover < best_remaining:
                    best_remaining = leftover
                    best_vehicle = i

        # No feasible vehicle
        if best_vehicle is None:
            return None

        # Assign customer
        routes[best_vehicle].append(customer_id)

        remaining_capacity[best_vehicle] -= demand

    # Close routes and remove unused vehicles
    final_routes = []

    for route in routes:

        if len(route) > 1:
            route.append(0)
            final_routes.append(route)

    return final_routes