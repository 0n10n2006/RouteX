import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..qpso import QPSO
from ..greedy_vrp import greedy_vrp
from ..hybrid import hybrid_qpso
from ..scenarios import create_scenarios
from ..fitness import fitness
from ..problem import ProblemInstance

from .database import create_tables, save_result, get_results
from .scenarios_ali import create_extra_scenarios
app = FastAPI(
    title="RouteX API",
    description="Quantum-Inspired Intelligent Traffic Route Optimization",
    version="1.0.0"
)


# Allow the frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # any origin — fine for local hackathon dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables when backend starts
create_tables()


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

# What the frontend sends to POST /optimize.
# "algorithm" chooses which optimizer to run. Defaults to "qpso".
# "scenario" chooses the problem to solve: default / low / medium / high.
class OptimizeRequest(BaseModel):
    algorithm: str = "qpso"
    scenario: str = "default"


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
def optimize(request: OptimizeRequest):

    # ----------------------------------------------
    # Choose the problem to solve based on "scenario"
    # ----------------------------------------------
    #
    # "default" -> the small hardcoded 5-node test problem.
    # "low" / "medium" / "high" -> teammates' scenarios.py presets
    #    (same road, higher customer demand each step).

    scenario_name = request.scenario.lower().strip()
    scenarios = create_scenarios()
    # Merge in Ali's harder scenarios (e.g. "big") on top of the team presets.
    scenarios.update(create_extra_scenarios())

    if scenario_name in scenarios:
        problem = scenarios[scenario_name]
    else:
        scenario_name = "default"

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


    # ----------------------------------------------
    # Pick the algorithm based on the request
    # ----------------------------------------------

    algo = request.algorithm.lower()

    # Start the stopwatch just before running the optimizer
    start_time = time.perf_counter()

    if algo == "greedy":

        # Classical baseline: one-shot nearest-neighbour VRP.
        # It returns routes only, so we compute fitness ourselves.
        routes = greedy_vrp(problem)
        best_fitness = fitness(routes, problem)

        # Classical is one-shot, so there is no convergence curve.
        convergence = []
        algorithm_name = "Greedy (classical baseline)"

    elif algo == "hybrid":

        # Flagship: QPSO first, then 2-opt local search refines its best route.
        result = hybrid_qpso(problem)

        best_fitness = result["fitness"]
        convergence = []
        algorithm_name = "Hybrid QPSO + 2-opt"

    else:

        # Default: QPSO (quantum-inspired). Runs for 20 iterations.
        qpso = QPSO(
            num_particles=5,
            num_customers=len(problem.customers)
        )

        for _ in range(20):
            qpso.step(
                problem,
                fitness,
                beta=0.5
            )

        best_fitness = qpso.global_best_fitness
        convergence = qpso.convergence
        algorithm_name = "QPSO"

    # Stop the stopwatch. runtime = how many seconds the algorithm took.
    runtime = time.perf_counter() - start_time

    # For now fitness IS the total distance, so distance == best_fitness.
    # (Kept as its own field so it can diverge later if fitness adds penalties.)
    distance = best_fitness


    # ----------------------------------------------
    # Save result in database
    # ----------------------------------------------

    save_result(
        algorithm_name,
        best_fitness,
        distance=distance,
        runtime=runtime,
        scenario=scenario_name
    )


    # ----------------------------------------------
    # Return result to frontend
    # ----------------------------------------------

    return {
        "algorithm": algorithm_name,
        "scenario": scenario_name,
        "fitness": best_fitness,
        "distance": distance,
        "runtime": runtime,
        "convergence": convergence
    }


# --------------------------------------------------
# GET PREVIOUS RESULTS
# --------------------------------------------------

@app.get("/results")
def results():

    return {
        "results": get_results()
    }


# --------------------------------------------------
# COMPARE ALGORITHMS
# --------------------------------------------------

@app.get("/results/comparison")
def results_comparison():

    rows = get_results()

    # Group saved runs by (scenario, algorithm), keeping the best (lowest)
    # fitness and the fastest runtime for each pair.
    summary = {}

    for row in rows:
        algo = row["algorithm"]
        score = row["fitness"]
        run_time = row["runtime"]
        scenario = row["scenario"] or "default"

        if score is None:
            continue

        key = (scenario, algo)

        if key not in summary:
            summary[key] = {
                "scenario": scenario,
                "algorithm": algo,
                "best_fitness": score,
                "best_runtime": run_time,
                "runs": 0
            }

        summary[key]["runs"] += 1

        if score < summary[key]["best_fitness"]:
            summary[key]["best_fitness"] = score

        # Track the fastest recorded runtime for this pair
        if run_time is not None:
            current = summary[key]["best_runtime"]
            if current is None or run_time < current:
                summary[key]["best_runtime"] = run_time

    # Sort by scenario, then best fitness (best algorithm first within a scenario)
    ranked = sorted(
        summary.values(),
        key=lambda item: (item["scenario"], item["best_fitness"])
    )

    return {
        "comparison": ranked
    }