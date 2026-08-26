def decode_random_keys(keys):
    """
    Convert random-key representation into customer order.
    """

    customer_order = sorted(
        range(len(keys)),
        key=lambda i: keys[i]
    )

    return [i + 1 for i in customer_order]

keys = [0.72, 0.13, 0.91, 0.44, 0.27]

route = decode_random_keys(keys)

print("Keys:", keys)
print("Decoded customer order:", route)

def decode_random_keys(keys):
    """
    Convert random keys into customer visit order.
    """

    customer_order = sorted(
        range(len(keys)),
        key=lambda i: keys[i]
    )

    return [i + 1 for i in customer_order]



def create_routes(customer_order, num_vehicles):
    """
    Split customer order between vehicles.
    """

    routes = [[] for _ in range(num_vehicles)]

    for i, customer in enumerate(customer_order):
        vehicle = i % num_vehicles
        routes[vehicle].append(customer)

    # Add depot at beginning and end
    routes = [
        [0] + route + [0]
        for route in routes
    ]

    return routes

if __name__ == "__main__":

    keys = [0.72, 0.13, 0.91, 0.44, 0.27]

    customer_order = decode_random_keys(keys)

    routes = create_routes(
        customer_order,
        num_vehicles=2
    )

    print("Keys:", keys)
    print("Customer order:", customer_order)
    print("Routes:", routes)