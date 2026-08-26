from problem import ProblemInstance
from fitness import fitness
from local_search import two_opt

distance_matrix = [
    [0, 10, 15, 20, 8],
    [10, 0, 9, 12, 7],
    [15, 9, 0, 6, 11],
    [20, 12, 6, 0, 10],
    [8, 7, 11, 10, 0]
]


problem = ProblemInstance(
    distance_matrix=distance_matrix,
    vehicles=[
        {"id": 1, "capacity": 10},
        {"id": 2, "capacity": 10}
    ],
    customers=[
        {"id": 1, "demand": 2},
        {"id": 2, "demand": 3},
        {"id": 3, "demand": 1},
        {"id": 4, "demand": 2}
    ]
)


solution = [
    [0, 1, 3, 2, 4, 0],
    [0, 4, 2, 3, 1, 0]
]


print("Before:", fitness(solution, problem))

improved, score = two_opt(
    solution,
    problem,
    fitness
)

print("After:", fitness(improved, problem))
print("Improved solution:", improved)