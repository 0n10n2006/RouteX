def decode_random_keys(keys):

    customer_order = sorted(
        range(len(keys)),
        key=lambda i: keys[i]
    )

    return [
        i + 1
        for i in customer_order
    ]


def create_routes(customer_order, problem):

    routes = []
    current_route = []
    current_load = 0
    vehicle_index = 0

    for customer_id in customer_order:

        demand = 0

        for customer in problem.customers:

            if customer["id"] == customer_id:

                demand = customer["demand"]
                break

        if vehicle_index >= len(problem.vehicles):
            return None

        vehicle_capacity = (
            problem.vehicles[
                vehicle_index
            ]["capacity"]
        )

        if current_load + demand <= vehicle_capacity:

            current_route.append(customer_id)
            current_load += demand

        else:

            if current_route:

                routes.append(
                    [0]
                    + current_route
                    + [0]
                )

            vehicle_index += 1

            if vehicle_index >= len(problem.vehicles):
                return None

            current_route = [customer_id]
            current_load = demand

    if current_route:

        routes.append(
            [0]
            + current_route
            + [0]
        )

    return routes