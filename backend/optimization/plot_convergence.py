import matplotlib.pyplot as plt

from problem import ProblemInstance
from qpso import QPSO
from fitness import fitness


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


qpso = QPSO(
    num_particles=10,
    num_customers=len(problem.customers)
)


for _ in range(20):

    qpso.step(
        problem,
        fitness,
        beta=0.5
    )


iterations = range(
    1,
    len(qpso.convergence) + 1
)

plt.plot(
    iterations,
    qpso.convergence,
    marker="o"
)

plt.xlabel("Iteration")
plt.ylabel("Best Fitness")
plt.title("QPSO Convergence")

plt.grid(True)

plt.savefig(
    "qpso_convergence.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()