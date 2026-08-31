"""RouteX FastAPI backend.

Owned by Ali (backend / database / integration).

Flow:  Frontend -> FastAPI -> optimizer -> result -> SQLite -> JSON -> Frontend
The frontend never calls the optimizers directly.

NOTE ON DATA: the distance matrices used here are still hand-written TEST
data. They get replaced by real road distances once Zobiya's
traffic/graph_builder.py can turn an OSMnx/NetworkX graph into a distance
matrix. Everything else in this pipeline stays the same when that happens.
"""

import math
import random
import statistics
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..qpso import QPSO
from ..greedy_vrp import greedy_vrp
from ..hybrid import hybrid_qpso
from ..scenarios import create_scenarios
from ..fitness import fitness
from ..problem import ProblemInstance
from ..constraints import check_customer_visits, check_depot, check_capacity

from .database import (
    create_tables,
    save_result,
    get_results,
    get_result,
    save_scenario,
    get_scenarios,
    get_scenario,
    get_scenario_by_name,
)
from .scenarios_ali import create_extra_scenarios


# --------------------------------------------------
# TUNABLE SETTINGS (Week 4 parameter tuning lives here)
# --------------------------------------------------

QPSO_PARTICLES = 10
QPSO_ITERATIONS = 20
QPSO_BETA = 0.5

# "greedy" is the classical baseline we measure improvement against.
BASELINE_ALGORITHM = "Greedy (classical baseline)"
ALL_ALGORITHMS = ["greedy", "qpso", "hybrid"]
BUILTIN_SCENARIOS = ["default", "low", "medium", "high", "big"]

app = FastAPI(
    title="RouteX API",
    description="Quantum-Inspired Intelligent Traffic Route Optimization",
    version="1.2.0"
)

# Allow the frontend (running on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # any origin — fine for local hackathon dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODELS (what the frontend is allowed to send)
# --------------------------------------------------

class OptimizeRequest(BaseModel):
    algorithm: str = "qpso"          # qpso | hybrid | greedy
    scenario: str = "default"        # default | low | medium | high | big | custom name
    seed: int | None = None          # set it to make a run reproducible


class BenchmarkRequest(BaseModel):
    seeds: int = 3                   # how many seeded repeats per combination
    scenarios: list[str] | None = None   # defaults to all built-in scenarios
    algorithms: list[str] | None = None  # defaults to all three algorithms


class ScenarioRequest(BaseModel):
    name: str
    distance_matrix: list
    vehicles: list
    customers: list
    description: str | None = None


# --------------------------------------------------
# SMALL HELPERS
# --------------------------------------------------

def clean_number(value):
    """Make a number safe to put in JSON.

    Algorithms return float("inf") when they fail to find a valid solution,
    but Infinity is NOT valid JSON and makes the browser's JSON.parse throw.
    We send null instead."""

    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isinf(number) or math.isnan(number):
        return None
    return number


def default_problem():
    """The original small 5-node test problem (kept as the 'default' scenario)."""

    return ProblemInstance(
        distance_matrix=[
            [0, 10, 15, 20, 8],
            [10, 0, 9, 12, 7],
            [15, 9, 0, 6, 11],
            [20, 12, 6, 0, 10],
            [8, 7, 11, 10, 0]
        ],
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


def builtin_problems():
    """Every scenario defined in Python: default + team presets + Ali's 'big'."""

    problems = {"default": default_problem()}
    problems.update(create_scenarios())        # low / medium / high (team)
    problems.update(create_extra_scenarios())  # big (Ali)
    return problems

def problem_from_scenario_row(row):
    """Turn a scenario saved in SQLite back into a ProblemInstance."""

    return ProblemInstance(
        distance_matrix=row["distance_matrix"],
        vehicles=row["vehicles"],
        customers=row["customers"],
    )


def build_problem(scenario_name):
    """Resolve a scenario name to a problem.

    Order of lookup:
      1. built-in Python scenarios (default / low / medium / high / big)
      2. custom scenarios saved in the database (created via POST /scenarios)
      3. fall back to 'default'

    Returns (resolved_name, problem)."""

    scenario_name = (scenario_name or "").lower().strip()

    problems = builtin_problems()
    if scenario_name in problems:
        return scenario_name, problems[scenario_name]

    row = get_scenario_by_name(scenario_name)
    if row is not None and row["customers"]:
        return row["name"], problem_from_scenario_row(row)

    return "default", default_problem()


def register_builtin_scenarios():
    """Copy the Python scenarios into the scenarios table on startup.

    This gives every scenario a stable numeric id the frontend can use, and
    is safe to run repeatedly (save_scenario updates instead of duplicating)."""

    descriptions = {
        "default": "Original 5-node smoke-test problem (4 customers, 2 vehicles)",
        "low": "Team preset — same road, low customer demand",
        "medium": "Team preset — same road, medium customer demand",
        "high": "Team preset — same road, high customer demand",
        "big": "Harder benchmark — 6 customers, 3 vehicles, capacity binds",
    }

    for name, problem in builtin_problems().items():
        save_scenario(
            name,
            distance_matrix=problem.distance_matrix,
            vehicles=problem.vehicles,
            customers=problem.customers,
            description=descriptions.get(name),
            source="builtin",
        )


# Create tables, then make sure the built-in scenarios exist.
create_tables()
register_builtin_scenarios()

# --------------------------------------------------
# RUNNING THE OPTIMIZERS (shared by /optimize and /benchmark)
# --------------------------------------------------

def count_violations(routes, problem):
    """How many of the three constraint rules this solution breaks.

    Uses Palak's checks from constraints.py — we only call them, never change
    them. Each check is guarded because a malformed route list (for example
    more routes than vehicles) would otherwise raise and kill the request."""

    if not routes:
        return 3      # no solution at all breaks everything

    violations = 0
    for check in (
        lambda: check_customer_visits(routes, problem),
        lambda: check_depot(routes),
        lambda: check_capacity(routes, problem),
    ):
        try:
            if not check():
                violations += 1
        except Exception:
            violations += 1

    return violations


def run_algorithm(algo, problem, seed=None):
    """Run ONE algorithm on ONE problem and measure it.

    Returns a dict with the algorithm name, routes, fitness, convergence
    curve, iteration count and runtime in seconds."""

    algo = (algo or "").lower().strip()

    # Seeding makes a run reproducible, which is what turns a demo number
    # into an experiment Akansha can repeat.
    if seed is not None:
        random.seed(seed)

    start_time = time.perf_counter()

    if algo == "greedy":
        # Classical baseline: one-shot nearest neighbour. Returns routes only,
        # so we compute the fitness ourselves.
        routes = greedy_vrp(problem) or []
        score = fitness(routes, problem) if routes else float("inf")
        convergence = []
        iterations = 0                    # one-shot: no iterations
        algorithm_name = "Greedy (classical baseline)"

    elif algo == "hybrid":
        # Flagship: QPSO explores globally, then 2-opt refines its best route.
        result = hybrid_qpso(
            problem,
            num_particles=QPSO_PARTICLES,
            iterations=QPSO_ITERATIONS,
            beta=QPSO_BETA,
        )
        if result is None:
            routes, score, convergence = [], float("inf"), []
        else:
            routes = result.get("routes") or []
            score = result.get("fitness", float("inf"))
            convergence = result.get("convergence") or []
        iterations = QPSO_ITERATIONS
        algorithm_name = "Hybrid QPSO + 2-opt"

    else:
        # Quantum-inspired QPSO — the technical centrepiece.
        qpso = QPSO(
            num_particles=QPSO_PARTICLES,
            num_customers=len(problem.customers),
        )
        for _ in range(QPSO_ITERATIONS):
            qpso.step(problem, fitness, beta=QPSO_BETA)

        best = qpso.get_best_solution(problem)
        routes = (best.get("routes") if best else None) or []
        score = qpso.global_best_fitness
        convergence = qpso.convergence
        iterations = QPSO_ITERATIONS
        algorithm_name = "QPSO"

    runtime = time.perf_counter() - start_time

    return {
        "algorithm": algorithm_name,
        "routes": routes,
        "fitness": score,
        "convergence": convergence,
        "iterations": iterations,
        "runtime": runtime,
    }

def run_and_save(algo, scenario_name, problem, seed=None):
    """Run one algorithm, store the full result in SQLite, return the JSON."""

    result = run_algorithm(algo, problem, seed=seed)

    routes = result["routes"]
    score = clean_number(result["fitness"])

    # For now fitness IS the total distance. Kept as a separate field because
    # once traffic is added, fitness will include penalties and the two differ.
    distance = score

    violations = count_violations(routes, problem)

    run_id = save_result(
        result["algorithm"],
        score,
        distance=distance,
        runtime=result["runtime"],
        scenario=scenario_name,
        routes=routes,
        convergence=[clean_number(value) for value in result["convergence"]],
        iterations=result["iterations"],
        constraint_violations=violations,
        vehicles_used=len(routes),
        seed=seed,
        # travel_time / congestion_penalty / fuel_cost stay NULL until
        # Zobiya's traffic model exists. We do not invent those numbers.
    )

    return {
        "run_id": run_id,
        "algorithm": result["algorithm"],
        "scenario": scenario_name,
        "fitness": score,
        "distance": distance,
        "runtime": result["runtime"],
        "routes": routes,
        "vehicles_used": len(routes),
        "iterations": result["iterations"],
        "constraint_violations": violations,
        "feasible": violations == 0,
        "seed": seed,
        "convergence": [clean_number(value) for value in result["convergence"]],
    }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "RouteX Backend is running!",
        "algorithms": ALL_ALGORITHMS,
        "scenarios": BUILTIN_SCENARIOS,
    }


# --------------------------------------------------
# OPTIMIZATION
# --------------------------------------------------

@app.post("/optimize")
def optimize(request: OptimizeRequest):
    """Run one algorithm on one scenario, save it, and return the result."""

    scenario_name, problem = build_problem(request.scenario)

    return run_and_save(
        request.algorithm,
        scenario_name,
        problem,
        seed=request.seed,
    )

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

@app.get("/results")
def results(limit: int | None = None):
    """Every saved run, newest first. Optional ?limit=20."""

    return {"results": get_results(limit=limit)}


# IMPORTANT: this must stay ABOVE /results/{run_id}, otherwise FastAPI would
# try to read the word "comparison" as a run id.
@app.get("/results/comparison")
def results_comparison():
    """Best fitness and fastest runtime per (scenario, algorithm)."""

    summary = {}

    for row in get_results():
        score = row["fitness"]
        if score is None:
            continue

        scenario = row["scenario"] or "default"
        key = (scenario, row["algorithm"])

        if key not in summary:
            summary[key] = {
                "scenario": scenario,
                "algorithm": row["algorithm"],
                "best_fitness": score,
                "best_runtime": row["runtime"],
                "runs": 0,
            }

        entry = summary[key]
        entry["runs"] += 1

        if score < entry["best_fitness"]:
            entry["best_fitness"] = score

        run_time = row["runtime"]
        if run_time is not None:
            if entry["best_runtime"] is None or run_time < entry["best_runtime"]:
                entry["best_runtime"] = run_time

    ranked = sorted(
        summary.values(),
        key=lambda item: (item["scenario"], item["best_fitness"]),
    )

    return {"comparison": ranked}


@app.get("/results/{run_id}")
def result_detail(run_id: int):
    """One saved run, including its routes — this is what draws the map."""

    row = get_result(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No run with id {run_id}")

    return row


@app.get("/results/{run_id}/convergence")
def result_convergence(run_id: int):
    """The convergence curve of one run — this is what draws the chart."""

    row = get_result(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No run with id {run_id}")

    convergence = row.get("convergence") or []

    return {
        "run_id": run_id,
        "algorithm": row["algorithm"],
        "scenario": row["scenario"],
        "iterations": row.get("iterations"),
        "convergence": convergence,
    }

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------

@app.get("/scenarios")
def scenarios_list():
    """All known scenarios with their stable numeric ids.

    Parag can use this to fill the scenario dropdown instead of hardcoding
    names in the frontend."""

    return {"scenarios": get_scenarios()}


@app.post("/scenarios")
def scenario_create(request: ScenarioRequest):
    """Create (or update) a custom scenario.

    Creating a scenario named the same as an existing one overwrites it.
    Custom scenarios can be optimized straight away by passing their name
    as the "scenario" field of POST /optimize."""

    name = request.name.lower().strip()

    if not name:
        raise HTTPException(status_code=400, detail="Scenario name is required")

    if not request.customers or not request.vehicles:
        raise HTTPException(
            status_code=400,
            detail="A scenario needs at least one vehicle and one customer",
        )

    # The matrix must cover the depot (0) plus every customer id.
    size = len(request.distance_matrix)
    highest_id = max(customer.get("id", 0) for customer in request.customers)
    if size <= highest_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"distance_matrix is {size}x{size} but customer id {highest_id} "
                f"needs at least {highest_id + 1} rows (row 0 is the depot)"
            ),
        )

    scenario_id = save_scenario(
        name,
        distance_matrix=request.distance_matrix,
        vehicles=request.vehicles,
        customers=request.customers,
        description=request.description,
        source="custom",
    )

    return {"scenario_id": scenario_id, "scenario": get_scenario(scenario_id)}


@app.get("/scenarios/{identifier}")
def scenario_detail(identifier: str):
    """One scenario, looked up by numeric id OR by name."""

    row = None
    if identifier.isdigit():
        row = get_scenario(int(identifier))
    if row is None:
        row = get_scenario_by_name(identifier.lower().strip())

    if row is None:
        raise HTTPException(status_code=404, detail=f"No scenario '{identifier}'")

    return row

# --------------------------------------------------
# BENCHMARK (Week 6 evidence)
# --------------------------------------------------

def summarise_trials(trials):
    """Group individual runs into per-(scenario, algorithm) statistics."""

    grouped = {}

    for trial in trials:
        key = (trial["scenario"], trial["algorithm"])
        grouped.setdefault(key, []).append(trial)

    summary = []

    for (scenario, algorithm), runs in grouped.items():
        scores = [run["fitness"] for run in runs if run["fitness"] is not None]
        runtimes = [run["runtime"] for run in runs if run["runtime"] is not None]

        summary.append({
            "scenario": scenario,
            "algorithm": algorithm,
            "runs": len(runs),
            "feasible_runs": sum(1 for run in runs if run["feasible"]),
            "best_fitness": min(scores) if scores else None,
            "mean_fitness": round(statistics.mean(scores), 2) if scores else None,
            "worst_fitness": max(scores) if scores else None,
            "mean_runtime": round(statistics.mean(runtimes), 5) if runtimes else None,
            "improvement_vs_baseline_percent": None,   # filled in below
        })

    # How much better than the classical baseline, per scenario. This is the
    # single number that proves the quantum-inspired approach is worth it.
    baselines = {
        entry["scenario"]: entry["mean_fitness"]
        for entry in summary
        if entry["algorithm"] == BASELINE_ALGORITHM
    }

    for entry in summary:
        baseline = baselines.get(entry["scenario"])
        if baseline and entry["mean_fitness"] is not None and baseline > 0:
            improvement = (baseline - entry["mean_fitness"]) / baseline * 100
            entry["improvement_vs_baseline_percent"] = round(improvement, 1)

    # Best (lowest) mean fitness first, within each scenario.
    summary.sort(
        key=lambda entry: (
            entry["scenario"],
            entry["mean_fitness"] if entry["mean_fitness"] is not None else float("inf"),
        )
    )

    return summary

@app.post("/benchmark")
def benchmark(request: BenchmarkRequest | None = None):
    """Run every algorithm on every scenario, several seeds each, and save all.

    This is the Week-6 harness: one call produces the whole
    classical-vs-quantum-inspired comparison table, with repeated seeds so the
    numbers are averages instead of one lucky run."""

    request = request or BenchmarkRequest()

    # Cap the work so a stray request can't hang the server.
    seeds = max(1, min(request.seeds, 10))
    scenario_names = request.scenarios or BUILTIN_SCENARIOS
    algorithms = request.algorithms or ALL_ALGORITHMS

    started = time.perf_counter()
    trials = []

    for scenario_name in scenario_names:
        resolved_name, problem = build_problem(scenario_name)

        for algo in algorithms:
            for index in range(seeds):
                # Fixed, predictable seeds so the whole benchmark is repeatable.
                result = run_and_save(
                    algo,
                    resolved_name,
                    problem,
                    seed=1000 + index,
                )
                trials.append({
                    "run_id": result["run_id"],
                    "scenario": result["scenario"],
                    "algorithm": result["algorithm"],
                    "fitness": result["fitness"],
                    "runtime": result["runtime"],
                    "feasible": result["feasible"],
                    "seed": result["seed"],
                })

    total_runtime = time.perf_counter() - started

    return {
        "total_runs": len(trials),
        "seeds_per_combination": seeds,
        "scenarios": scenario_names,
        "algorithms": algorithms,
        "total_runtime": round(total_runtime, 3),
        "summary": summarise_trials(trials),
        "runs": trials,
    }
