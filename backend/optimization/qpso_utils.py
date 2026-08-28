def decode_random_keys(keys):
    """
    Convert random-key representation into customer order.
    """

    customer_order = sorted(
        range(len(keys)),
        key=lambda i: keys[i]
    )

    return [i + 1 for i in customer_order]

def create_routes(customer_order, problem):
    """
    Split customer order into feasible routes based on
    vehicle capacity.

    Only active routes are returned.
    """

    routes = []
    current_route = []
    current_load = 0

    vehicle_index = 0

    for customer_id in customer_order:

        # Find customer demand
        demand = 0

        for customer in problem.customers:
            if customer["id"] == customer_id:
                demand = customer["demand"]
                break

        # No vehicles left
        if vehicle_index >= len(problem.vehicles):
            return None

        vehicle_capacity = problem.vehicles[
            vehicle_index
        ]["capacity"]

        # Customer fits in current vehicle
        if current_load + demand <= vehicle_capacity:

            current_route.append(customer_id)
            current_load += demand

        else:

            # Finish current route
            if current_route:
                routes.append(
                    [0] + current_route + [0]
                )

            # Move to next vehicle
            vehicle_index += 1

            if vehicle_index >= len(problem.vehicles):
                return None

            # Start new route
            current_route = [customer_id]
            current_load = demand

    # Add final route
    if current_route:
        routes.append(
            [0] + current_route + [0]
        )

    return routes

if __name__ == "__main__":

    from problem import ProblemInstance

    keys = [0.72, 0.13, 0.91, 0.44, 0.27]

    customer_order = decode_random_keys(keys)

    problem = ProblemInstance(
        distance_matrix=[],

        vehicles=[
            {"id": 1, "capacity": 5},
            {"id": 2, "capacity": 5}
        ],

        customers=[
            {"id": 1, "demand": 2},
            {"id": 2, "demand": 3},
            {"id": 3, "demand": 1},
            {"id": 4, "demand": 2},
            {"id": 5, "demand": 2}
        ]
    )

    routes = create_routes(
        customer_order,
        problem
    )

    print("Keys:", keys)
    print("Customer order:", customer_order)
    print("Routes:", routes)