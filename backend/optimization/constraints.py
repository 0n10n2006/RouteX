def check_customer_visits(solution, problem):
    customer_ids = {customer["id"] for customer in problem.customers}

    visited_customers = []

    for route in solution:
        for customer in route:
            if customer != 0:
                visited_customers.append(customer)

    all_customers_present = (
        set(visited_customers) == customer_ids
    )

    no_duplicates = (
        len(visited_customers) == len(set(visited_customers))
    )

    return all_customers_present and no_duplicates

def check_depot(solution):
    for route in solution:

        if len(route) < 2:
            return False

        if route[0] != 0:
            return False

        if route[-1] != 0:
            return False

    return True

def check_capacity(solution, problem):
    for i, route in enumerate(solution):

        vehicle = problem.vehicles[i]
        capacity = vehicle["capacity"]

        total_demand = 0

        for customer_id in route:

            if customer_id != 0:

                for customer in problem.customers:

                    if customer["id"] == customer_id:
                        total_demand += customer["demand"]
                        break

        if total_demand > capacity:
            return False

    return True

def validate(solution, problem):

    if not check_customer_visits(solution, problem):
        return False

    if not check_depot(solution):
        return False

    if not check_capacity(solution, problem):
        return False

    return True