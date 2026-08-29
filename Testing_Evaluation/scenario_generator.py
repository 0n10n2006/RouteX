# Scenario Generator


scenarios = [
    {
        "id": "S1",
        "demand": "Low",
        "traffic": "Low",
        "incident": False,
        "vehicles": 3,
        "delivery_points": 10
    },

    {
        "id": "S2",
        "demand": "Medium",
        "traffic": "Medium",
        "incident": False,
        "vehicles": 5,
        "delivery_points": 15
    },

    {
        "id": "S3",
        "demand": "High",
        "traffic": "High",
        "incident": False,
        "vehicles": 10,
        "delivery_points": 25
    },

    {
        "id": "S4",
        "demand": "Medium",
        "traffic": "High",
        "incident": True,
        "vehicles": 5,
        "delivery_points": 15
    },

    {
        "id": "S5",
        "demand": "High",
        "traffic": "High",
        "incident": True,
        "vehicles": 10,
        "delivery_points": 25
    }
]


# Display all scenarios

for scenario in scenarios:
    print("Scenario:", scenario["id"])
    print("Demand:", scenario["demand"])
    print("Traffic:", scenario["traffic"])
    print("Incident:", scenario["incident"])
    print("Vehicles:", scenario["vehicles"])
    print("Delivery Points:", scenario["delivery_points"])
    print("-------------------------")