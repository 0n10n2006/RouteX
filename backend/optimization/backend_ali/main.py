from fastapi import FastAPI

from qpso import QPSO
from fitness import fitness
from problem import ProblemInstance

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "RouteX Backend is running!"
    }


@app.post("/optimize")
def optimize():

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]

    vehicles = [
        {"id": 1, "capacity": 10},
        {"id": 2, "capacity": 10}
    ]

    customers = [
        {"id": 1, "demand": 2},
        {"id": 2, "demand": 3},
        {"id": 3, "demand": 1},
        {"id": 4, "demand": 2}
    ]

    problem = ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )

    qpso = QPSO(
        num_particles=5,
        num_customers=len(customers)
    )

    for _ in range(20):
        qpso.step(
            problem,
            fitness,
            beta=0.5
        )

    return {
        "algorithm": "QPSO",
        "fitness": qpso.global_best_fitness,
        "convergence": qpso.convergence
    }