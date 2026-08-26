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