from fastapi import FastAPI

from qpso import QPSO
from fitness import fitness
from problem import ProblemInstance

from .database import create_tables, save_result, get_results


app = FastAPI(
    title="RouteX API",
    description="Quantum-Inspired Intelligent Traffic Route Optimization",
    version="1.0.0"
)


# Create database tables when backend starts
create_tables()


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "RouteX Backend is running!"
    }


# --------------------------------------------------
# OPTIMIZATION
# --------------------------------------------------

@app.post("/optimize")
def optimize():

    # ----------------------------------------------
    # Test distance matrix
    # ----------------------------------------------

    distance_matrix = [
        [0, 10, 15, 20, 8],
        [10, 0, 9, 12, 7],
        [15, 9, 0, 6, 11],
        [20, 12, 6, 0, 10],
        [8, 7, 11, 10, 0]
    ]


    # ----------------------------------------------
    # Vehicles
    # ----------------------------------------------

    vehicles = [
        {
            "id": 1,
            "capacity": 10
        },
        {
            "id": 2,
            "capacity": 10
        }
    ]


    # ----------------------------------------------
    # Customers
    # ----------------------------------------------

    customers = [
        {
            "id": 1,
            "demand": 2
        },
        {
            "id": 2,
            "demand": 3
        },
        {
            "id": 3,
            "demand": 1
        },
        {
            "id": 4,
            "demand": 2
        }
    ]


    # ----------------------------------------------
    # Create problem instance
    # ----------------------------------------------

    problem = ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers
    )


    # ----------------------------------------------
    # Create QPSO
    # ----------------------------------------------

    qpso = QPSO(
        num_particles=5,
        num_customers=len(customers)
    )


    # ----------------------------------------------
    # Run QPSO
    # ----------------------------------------------

    for _ in range(20):

        qpso.step(
            problem,
            fitness,
            beta=0.5
        )


    # ----------------------------------------------
    # Get final fitness
    # ----------------------------------------------

    best_fitness = qpso.global_best_fitness


    # ----------------------------------------------
    # Save result in database
    # ----------------------------------------------

    save_result(
        "QPSO",
        best_fitness
    )


    # ----------------------------------------------
    # Return result to frontend
    # ----------------------------------------------

    return {
        "algorithm": "QPSO",
        "fitness": best_fitness,
        "convergence": qpso.convergence
    }


# --------------------------------------------------
# GET PREVIOUS RESULTS
# --------------------------------------------------

@app.get("/results")
def results():

    return {
        "results": get_results()
    }