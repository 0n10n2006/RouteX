"""RouteX FastAPI backend.

Owned by Ali (backend / database / integration).

Flow:  Frontend -> FastAPI -> optimizer -> result -> SQLite -> JSON -> Frontend
The frontend never calls the optimizers directly.

NOTE ON DATA: the distance matrices used here are still hand-written TEST
data. They get replaced by real road distances once Zobiya's
traffic/graph_builder.py can turn an OSMnx/NetworkX graph into a distance
matrix. Everything else in this pipeline stays the same when that happens.
"""
try:
    from dotenv import load_dotenv
except ImportError:  # Optional for deployments that inject environment variables.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()
import math
import os
import tempfile
import random
import statistics
import time
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

from ..qpso import QPSO
from ..greedy_vrp import greedy_vrp
from ..hybrid import hybrid_qpso
from ..benchmark import run_ga, run_pso
from ..scenarios import create_scenarios
from ..fitness import calculate_metrics, fitness
from ..problem import ProblemInstance
from ..constraints import check_customer_visits, check_depot, check_capacity
from ..traffic_scenarios import (
    KOTHRUD_OSM_FILE,
    create_kothrud_problem,
    create_kothrud_live_traffic_problem,
    create_kothrud_problem_with_incident,
    resolve_kothrud_incident,
    create_larger_area_problem,
)
from traffic.live_traffic import LiveTrafficError
from traffic.graph_builder import build_route_geometry, build_route_matrix
from traffic.osm_loader import load_prepared_road_network, prepare_graph
from .database import (
    create_tables,
    save_result,
    get_results,
    get_results_comparison,
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

QPSO_PARTICLES = 14
QPSO_ITERATIONS = 50
GA_POPULATION_SIZE = 20
GA_GENERATIONS = 50
PSO_PARTICLES = 20
PSO_ITERATIONS = 50
# QPSO's beta (contraction-expansion coefficient) is annealed linearly from
# BETA_START down to BETA_END across the run: high beta early on means the
# swarm explores broadly, low beta later means it exploits/fine-tunes. This
# is what turns the convergence chart into a genuine multi-step decline
# instead of jumping straight to the optimum on iteration one. Hybrid QPSO
# keeps a single fixed beta (QPSO_BETA) since hybrid_qpso() doesn't accept
# a schedule.
QPSO_BETA = 0.5
QPSO_BETA_START = 1.0
QPSO_BETA_END = 0.2

# "greedy" is the classical baseline we measure improvement against.
BASELINE_ALGORITHM = "Greedy (classical baseline)"
ALL_ALGORITHMS = ["greedy", "ga", "pso", "qpso", "hybrid"]
BUILTIN_SCENARIOS = ["default", "low", "medium", "high", "big", "kothrud", "larger_area"]
LIVE_TRAFFIC_SCENARIO = "kothrud_live"

app = FastAPI(
    title="RouteX API",
    description="Quantum-Inspired Intelligent Traffic Route Optimization",
    version="1.2.0"
)

# Initialize Firebase Admin for token verification.
# On Render, set FIREBASE_SERVICE_ACCOUNT_KEY to the full JSON content of
# your Firebase service account key (Project Settings > Service Accounts >
# Generate New Private Key).  Locally, ADC from `gcloud auth` is used.
# Initialize Firebase Admin for token verification.
# On Render, set FIREBASE_SERVICE_ACCOUNT_KEY to the full JSON content of
# your Firebase service account key (Project Settings > Service Accounts >
# Generate New Private Key).  Locally, ADC from `gcloud auth` is used.
try:
    firebase_admin.get_app()
except ValueError:
    import json as _json, base64 as _base64

    _sa_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY", "").strip()
    if _sa_key:
        # Accept raw JSON or base64-encoded JSON
        try:
            _sa_dict = _json.loads(_sa_key)
        except _json.JSONDecodeError:
            _sa_dict = _json.loads(_base64.b64decode(_sa_key))
        cred = credentials.Certificate(_sa_dict)
        firebase_admin.initialize_app(cred)
    else:
        # Local dev — rely on Application Default Credentials
        firebase_admin.initialize_app(options={'projectId': 'routex-auth'})
    import json as _json, base64 as _base64

    _sa_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY", "").strip()
    if _sa_key:
        # Accept raw JSON or base64-encoded JSON
        try:
            _sa_dict = _json.loads(_sa_key)
        except _json.JSONDecodeError:
            _sa_dict = _json.loads(_base64.b64decode(_sa_key))
        cred = credentials.Certificate(_sa_dict)
        firebase_admin.initialize_app(cred)
    else:
        # Local dev — rely on Application Default Credentials
        firebase_admin.initialize_app(options={'projectId': 'routex-auth'})

def get_current_user(authorization: str = Header(None)):
    """FastAPI Dependency to verify Firebase ID token and return user info."""
    if not authorization or not authorization.startswith("Bearer "):
        # For development/simplicity, we won't strictly block unauthenticated users
        # on every endpoint unless we enforce it, but we can return None.
        return None
    
    token = authorization.split(" ")[1]
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token # dict containing 'uid', 'email', etc.
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None

# Allow the frontend (running on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # any origin â€” fine for local hackathon dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODELS (what the frontend is allowed to send)
# --------------------------------------------------

class OptimizeRequest(BaseModel):
    algorithm: str = "qpso"          # greedy | ga | pso | qpso | hybrid
    scenario: str = "default"        # default | low | medium | high | big | custom name
    seed: int | None = None          # set it to make a run reproducible


class BenchmarkRequest(BaseModel):
    seeds: int = 3                   # how many seeded repeats per combination
    scenarios: list[str] | None = None   # defaults to all built-in scenarios
    algorithms: list[str] | None = None  # defaults to all supported algorithms


class IncidentOptimizeRequest(BaseModel):
    algorithm: str = "qpso"
    seed: int | None = None
    incident_factor: float = 0.25
    incident_edge: list[int] | None = None
    incident_scenario: str | None = None


class CustomLocation(BaseModel):
    id: int
    name: str = ""
    latitude: float
    longitude: float
    type: str = "customer"     # "depot" or "customer"
    demand: int = 1


class CustomVehicle(BaseModel):
    id: int
    capacity: int = 10


class CustomOptimizeRequest(BaseModel):
    locations: list[CustomLocation]
    vehicles: list[CustomVehicle]
    algorithm: str = "qpso"
    seed: int | None = None


class ScenarioRequest(BaseModel):
    name: str
    distance_matrix: list
    travel_time_matrix: list | None = None
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


@lru_cache(maxsize=1)
def matrix_builtin_problems():
    """Build the small matrix scenarios once per backend process."""
    problems = {"default": default_problem()}
    problems.update(create_scenarios())
    problems.update(create_extra_scenarios())
    return problems


@lru_cache(maxsize=1)
def kothrud_problem():
    """Build the Kothrud OSM scenario once, on its first request."""
    return create_kothrud_problem()


@lru_cache(maxsize=1)
def larger_area_problem():
    """Build the larger OSM scenario once, on its first request."""
    return create_larger_area_problem()


def builtin_problems():
    """Return every built-in problem for callers that need the full catalog."""
    return {
        **matrix_builtin_problems(),
        "kothrud": kothrud_problem(),
        "larger_area": larger_area_problem(),
    }


def get_builtin_problem(scenario_name):
    """Resolve one built-in scenario without constructing unrelated OSM maps."""
    matrix_problem = matrix_builtin_problems().get(scenario_name)
    if matrix_problem is not None:
        return matrix_problem
    if scenario_name == "kothrud":
        return kothrud_problem()
    if scenario_name == "larger_area":
        return larger_area_problem()
    return None


def problem_from_scenario_row(row):
    """Turn a scenario saved in SQLite back into a ProblemInstance."""

    return ProblemInstance(
        distance_matrix=row["distance_matrix"],
        travel_time_matrix=row["travel_time_matrix"],
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

    if scenario_name == LIVE_TRAFFIC_SCENARIO:
        return scenario_name, create_kothrud_live_traffic_problem()

    problem = get_builtin_problem(scenario_name)
    if problem is not None:
        return scenario_name, problem

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
        "low": "Team preset â€” same road, low customer demand",
        "medium": "Team preset â€” same road, medium customer demand",
        "high": "Team preset â€” same road, high customer demand",
        "big": "Harder benchmark â€” 6 customers, 3 vehicles, capacity binds",
        "kothrud": (
            "Real Kothrud OSM road extract â€” 4 customers, 2 vehicles; "
            "traffic speeds are simulated"
        ),
        "larger_area": (
            "Larger real OSM road extract â€” 8 customers, 3 vehicles; "
            "bigger search space, traffic speeds are simulated"
        ),
    }

    # Register only matrix scenarios at startup. OSM matrices are expensive
    # to derive; scenario_detail registers one lazily if it is requested.
    for name, problem in matrix_builtin_problems().items():
        save_scenario(
            name,
            distance_matrix=problem.distance_matrix,
            travel_time_matrix=problem.travel_time_matrix,
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

    Uses Palak's checks from constraints.py â€” we only call them, never change
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

    elif algo == "ga":
        # Classical evolutionary baseline supplied by the optimization team.
        result = run_ga(
            problem,
            population_size=GA_POPULATION_SIZE,
            generations=GA_GENERATIONS,
        )
        routes = result["routes"] or []
        score = result["fitness"]
        convergence = []  # GA currently exposes no generation-wise curve.
        iterations = GA_GENERATIONS
        algorithm_name = "GA"

    elif algo == "pso":
        # Classical particle swarm baseline supplied by the optimization team.
        result = run_pso(
            problem,
            num_particles=PSO_PARTICLES,
            iterations=PSO_ITERATIONS,
        )
        routes = result["routes"] or []
        score = result["fitness"]
        convergence = []  # PSO currently exposes no iteration-wise curve.
        iterations = PSO_ITERATIONS
        algorithm_name = "PSO"

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

    elif algo == "qpso":
        # Quantum-inspired QPSO â€” the technical centrepiece.
        qpso = QPSO(
            num_particles=QPSO_PARTICLES,
            num_customers=len(problem.customers),
        )
        for iteration in range(QPSO_ITERATIONS):
            # Anneal beta from BETA_START (exploratory) to BETA_END
            # (exploitative) so the convergence curve shows real,
            # multi-step progress instead of flattening on iteration one.
            progress = iteration / max(QPSO_ITERATIONS - 1, 1)
            beta = QPSO_BETA_START - (QPSO_BETA_START - QPSO_BETA_END) * progress
            qpso.step(problem, fitness, beta=beta)

        best = qpso.get_best_solution(problem)
        routes = (best.get("routes") if best else None) or []
        score = qpso.global_best_fitness
        convergence = qpso.convergence
        iterations = QPSO_ITERATIONS
        algorithm_name = "QPSO"
    else:
        raise ValueError(
            "Unknown algorithm. Choose one of: " + ", ".join(ALL_ALGORITHMS)
        )

    runtime = time.perf_counter() - start_time

    return {
        "algorithm": algorithm_name,
        "routes": routes,
        "fitness": score,
        "convergence": convergence,
        "iterations": iterations,
        "runtime": runtime,
    }

def run_and_save(algo, scenario_name, problem, seed=None, user_id=None):
    """Run one algorithm, store the full result in SQLite, return the JSON."""

    result = run_algorithm(algo, problem, seed=seed)

    routes = result["routes"]
    score = clean_number(result["fitness"])

    # OSM scenarios optimise simulated traffic-adjusted travel time while
    # retaining independently measured road distance for reporting.
    metrics = calculate_metrics(routes, problem) if routes else {}
    distance = clean_number(metrics.get("distance"))
    travel_time = clean_number(metrics.get("travel_time"))

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
        travel_time=travel_time,
        traffic_metadata=problem.metadata,
        user_id=user_id,
    )

    return {
        "run_id": run_id,
        "algorithm": result["algorithm"],
        "scenario": scenario_name,
        "fitness": score,
        "distance": distance,
        "travel_time": travel_time,
        "runtime": result["runtime"],
        "routes": routes,
        "vehicles_used": len(routes),
        "iterations": result["iterations"],
        "constraint_violations": violations,
        "feasible": violations == 0,
        "seed": seed,
        "convergence": [clean_number(value) for value in result["convergence"]],
        "traffic_metadata": problem.metadata,
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
        "live_traffic_scenario": LIVE_TRAFFIC_SCENARIO,
    }


# --------------------------------------------------
# OPTIMIZATION
# --------------------------------------------------

@app.post("/optimize")
def optimize(request: OptimizeRequest, user: dict = Depends(get_current_user)):
    """Run one algorithm on one scenario, save it, and return the result."""
    
    user_id = user['uid'] if user else None

    try:
        scenario_name, problem = build_problem(request.scenario)
    except LiveTrafficError as error:
        raise HTTPException(status_code=503, detail=str(error))

    try:
        return run_and_save(
            request.algorithm,
            scenario_name,
            problem,
            seed=request.seed,
            user_id=user_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/optimize/custom")
def optimize_custom(request: CustomOptimizeRequest, user: dict = Depends(get_current_user)):
    """Run optimization on user-provided lat/lng locations anywhere in the world.

    Downloads the OSM road network covering all locations on the fly using
    downloads the OSM road network covering all locations on the fly using
    osmnx, builds distance and travel-time matrices from it, and runs the
    requested algorithm.  The frontend sends map clicks, not matrices.
    """
    user_id = user['uid'] if user else None
    if len(request.locations) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 locations are needed (1 depot + 1 customer)",
        )

    depots = [loc for loc in request.locations if loc.type == "depot"]
    customers_raw = [loc for loc in request.locations if loc.type == "customer"]
    if len(depots) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one depot is required",
        )
    if not customers_raw:
        raise HTTPException(
            status_code=400,
            detail="At least one customer location is required",
        )
    if not request.vehicles:
        raise HTTPException(
            status_code=400,
            detail="At least one vehicle is required",
        )

    # Re-index: depot gets id 0, customers get 1..N
    depot = depots[0]
    locations = [
        {"id": 0, "name": depot.name or "Depot",
         "latitude": depot.latitude, "longitude": depot.longitude},
    ]
    problem_customers = []
    for i, cust in enumerate(customers_raw, start=1):
        locations.append({
            "id": i,
            "name": cust.name or f"Customer {i}",
            "latitude": cust.latitude,
            "longitude": cust.longitude,
        })
        problem_customers.append({"id": i, "demand": max(cust.demand, 1)})

    problem_vehicles = [
        {"id": v.id, "capacity": max(v.capacity, 1)} for v in request.vehicles
    ]

    # Download OSM road network covering all points
    lats = [loc["latitude"] for loc in locations]
    lngs = [loc["longitude"] for loc in locations]
    center_lat = (min(lats) + max(lats)) / 2
    center_lng = (min(lngs) + max(lngs)) / 2

    # Radius: half-diagonal of the bounding box + generous padding
    from math import radians, cos, sqrt, asin, sin
    from math import radians, cos, sqrt, asin, sin
    dlat = max(lats) - min(lats)
    dlng = max(lngs) - min(lngs)
    lat_m = dlat * 111320
    lng_m = dlng * 111320 * cos(radians(center_lat))
    half_diagonal = sqrt(lat_m ** 2 + lng_m ** 2) / 2
    radius = max(half_diagonal * 1.5, 1500)  # at least 1.5 km

    # Try multiple Overpass API mirrors — the default (overpass-api.de) often
    # blocks cloud/datacenter IPs such as those used by Render.
    # Keep timeouts short so we fall back to haversine quickly rather than
    # exceeding Render's ~30s request timeout.
    import osmnx as ox
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    OVERPASS_MIRRORS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]

    graph = None
    last_error = None

    def _try_download(mirror_url):
        """Download graph from a single mirror (runs in thread for timeout)."""
        ox.settings.overpass_url = mirror_url
        ox.settings.requests_timeout = 10
        g = ox.graph_from_point(
            (center_lat, center_lng),
            dist=radius,
            network_type="drive",
            simplify=True,
        )
        return prepare_graph(g)

    for mirror_url in OVERPASS_MIRRORS:
        try:
            # Hard 12s wall-clock cap per mirror via thread executor
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_try_download, mirror_url)
                graph = future.result(timeout=12)
            break  # success
        except (FuturesTimeout, Exception) as error:
            last_error = error
            continue

    # Fallback: if all Overpass mirrors failed, build straight-line
    # (haversine) distance/time matrices so the optimizer still works.
    used_haversine_fallback = False
    if graph is None:
        used_haversine_fallback = True

        def _haversine_m(lat1, lon1, lat2, lon2):
            """Great-circle distance between two points in metres."""
            R = 6_371_000  # Earth radius in metres
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlam = radians(lon2 - lon1)
            a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
            return R * 2 * asin(sqrt(a))

        n = len(locations)
        fallback_dist = [[0.0] * n for _ in range(n)]
        fallback_time = [[0.0] * n for _ in range(n)]
        AVG_SPEED_MS = 30 * 1000 / 3600  # 30 km/h in m/s

        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                d = _haversine_m(
                    locations[i]["latitude"], locations[i]["longitude"],
                    locations[j]["latitude"], locations[j]["longitude"],
                )
                # Road distance is typically ~1.4x straight-line distance
                road_est = d * 1.4
                fallback_dist[i][j] = road_est
                fallback_time[i][j] = road_est / AVG_SPEED_MS

    # Build matrices — either from the real road graph or from haversine fallback
    if used_haversine_fallback:
        distance_matrix = fallback_dist
        travel_time_matrix = fallback_time
        matrix_metadata = {
            "distance_unit": "metres",
            "travel_time_unit": "seconds",
        }
        source_label = "Custom user locations with haversine distance (Overpass API unavailable)"
        osm_source_label = "haversine_fallback"
    else:
        try:
            matrix_data = build_route_matrix(graph, locations)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error))
        distance_matrix = matrix_data["distance_matrix"]
        travel_time_matrix = matrix_data["travel_time_matrix"]
        matrix_metadata = matrix_data["metadata"]
        source_label = "Custom user locations with OSM road network"
        osm_source_label = "osmnx.graph_from_point"

    problem = ProblemInstance(
        distance_matrix=distance_matrix,
        travel_time_matrix=travel_time_matrix,
        distance_matrix=distance_matrix,
        travel_time_matrix=travel_time_matrix,
        vehicles=problem_vehicles,
        customers=problem_customers,
        metadata={
            **matrix_metadata,
            "source": source_label,
            "osm_source": osm_source_label,
            **matrix_metadata,
            "source": source_label,
            "osm_source": osm_source_label,
            "traffic_factors": None,
            "locations": locations,
            "incident": None,
        },
    )

    try:
        result = run_and_save(
            request.algorithm, "custom", problem, seed=request.seed, user_id=user_id
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    # Attach geometry inline so frontend has it immediately
    if not used_haversine_fallback:
        try:
            geometry = build_route_geometry(
                graph, locations, result["routes"],
            )
            result["geometry"] = geometry
        except Exception:
            result["geometry"] = None
    else:
    if not used_haversine_fallback:
        try:
            geometry = build_route_geometry(
                graph, locations, result["routes"],
            )
            result["geometry"] = geometry
        except Exception:
            result["geometry"] = None
    else:
        result["geometry"] = None

    return result


@app.post("/optimize/kothrud-incident")
def optimize_kothrud_incident(request: IncidentOptimizeRequest):
    """Show a route before and after a simulated incident, then re-optimize.

    The incident is an explicit OSM edge or a stable named scenario. The same
    requested seed is passed to both runs for a reproducible comparison.
    """
    if not 0 < request.incident_factor <= 1:
        raise HTTPException(
            status_code=400,
            detail="incident_factor must satisfy 0 < factor <= 1",
        )

    before_problem = create_kothrud_problem()
    before = run_and_save(
        request.algorithm,
        "kothrud",
        before_problem,
        seed=request.seed,
    )

    try:
        selection = resolve_kothrud_incident(
            incident_edge=request.incident_edge,
            incident_scenario=request.incident_scenario,
        )
        incident_problem = create_kothrud_problem_with_incident(
            incident_edge=selection["edge"],
            incident_factor=request.incident_factor,
            incident_scenario=selection["scenario"],
            incident_description=selection["description"],
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    after = run_and_save(
        request.algorithm,
        "kothrud_incident",
        incident_problem,
        seed=request.seed,
    )

    return {
        "before": before,
        "after_incident": after,
        "incident": incident_problem.metadata["incident"],
        "traffic_metadata": {
            "before": before_problem.metadata,
            "after_incident": incident_problem.metadata,
        },
        "note": "OSM road geometry is real; traffic and incident speed reductions are simulated.",
    }

# --------------------------------------------------
# RESULTS
# --------------------------------------------------

@app.get("/results")
def results(limit: int | None = None, user: dict = Depends(get_current_user)):
    """Every saved run, newest first. Optional ?limit=20."""
    
    all_results = get_results(limit=limit)
    if user:
        # Admins can see all, regular users see only their own
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE firebase_uid = ?", (user['uid'],))
        row = cursor.fetchone()
        conn.close()
        
        is_admin = row and row['role'] == 'admin'
        if not is_admin:
            all_results = [r for r in all_results if r.get('user_id') == user['uid']]
            
    return {"results": all_results}


# IMPORTANT: this must stay ABOVE /results/{run_id}, otherwise FastAPI would
# try to read the word "comparison" as a run id.
@app.get("/results/comparison")
def results_comparison():
    """Best fitness and fastest runtime per (scenario, algorithm)."""
    return {"comparison": get_results_comparison()}


@app.get("/results/{run_id}")
def result_detail(run_id: int):
    """One saved run, including its routes â€” this is what draws the map."""

    row = get_result(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No run with id {run_id}")

    # POST /optimize exposes this derived field, and the React dashboard also
    # needs it when a user opens an older SQLite run from its history.
    row["feasible"] = row.get("constraint_violations") == 0

    return row


@app.get("/results/{run_id}/convergence")
def result_convergence(run_id: int):
    """The convergence curve of one run â€” this is what draws the chart."""

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


@app.get("/results/{run_id}/geometry")
def result_geometry(run_id: int):
    """Return real OSM road geometry for each vehicle route as GeoJSON.

    Only OSM-backed runs (Kothrud, the larger area extract, ...) include the
    required source locations and OSM file. Matrix-only scenarios
    intentionally cannot invent map geometry.
    """
    row = get_result(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No run with id {run_id}")

    metadata = row.get("traffic_metadata") or {}
    osm_file = metadata.get("osm_file")
    if not osm_file or not metadata.get("locations"):
        raise HTTPException(
            status_code=422,
            detail="Road geometry is available only for OSM-backed runs",
        )

    incident = metadata.get("incident") or {}
    incident_edges = None
    if incident.get("edge"):
        incident_edges = {
            tuple(incident["edge"]): incident.get("speed_factor", 1.0)
        }

    try:
        graph = load_prepared_road_network(osm_file)
        geometry = build_route_geometry(
            graph,
            metadata["locations"],
            row["routes"],
            traffic_factors=metadata.get("traffic_factors"),
            incident_edges=incident_edges,
        )
    except (KeyError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error))

    return {
        **geometry,
        "run_id": run_id,
        "scenario": row["scenario"],
        "locations": metadata["locations"],
        "incident": incident or None,
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

    # Matrices must cover the depot (0) plus every customer id.
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

    for row in request.distance_matrix:
        if not isinstance(row, list) or len(row) != size:
            raise HTTPException(
                status_code=400,
                detail="distance_matrix must be square",
            )

    if request.travel_time_matrix is not None:
        if len(request.travel_time_matrix) != size or any(
            not isinstance(row, list) or len(row) != size
            for row in request.travel_time_matrix
        ):
            raise HTTPException(
                status_code=400,
                detail="travel_time_matrix must be the same square size as distance_matrix",
            )

    scenario_id = save_scenario(
        name,
        distance_matrix=request.distance_matrix,
        travel_time_matrix=request.travel_time_matrix,
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

    # OSM matrices are intentionally built on demand so normal API startup
    # and matrix-only optimizations do not parse road-network XML files.
    if row is None and not identifier.isdigit():
        name = identifier.lower().strip()
        problem = get_builtin_problem(name)
        if problem is not None:
            save_scenario(
                name,
                distance_matrix=problem.distance_matrix,
                travel_time_matrix=problem.travel_time_matrix,
                vehicles=problem.vehicles,
                customers=problem.customers,
                source="builtin",
            )
            row = get_scenario_by_name(name)

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
    if LIVE_TRAFFIC_SCENARIO in scenario_names:
        raise HTTPException(
            status_code=400,
            detail=(
                "kothrud_live is a point-in-time traffic snapshot and cannot "
                "be benchmarked reproducibly. Run it through POST /optimize."
            ),
        )
    algorithms = [
        (algorithm or "").lower().strip()
        for algorithm in (request.algorithms or ALL_ALGORITHMS)
    ]
    unknown_algorithms = sorted(set(algorithms) - set(ALL_ALGORITHMS))
    if unknown_algorithms:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unknown algorithms: "
                + ", ".join(unknown_algorithms)
                + ". Choose from: "
                + ", ".join(ALL_ALGORITHMS)
            ),
        )

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

# --------------------------------------------------
# AUTH & USERS
# --------------------------------------------------

from .database import get_connection

@app.post("/auth/sync")
def sync_user(user: dict = Depends(get_current_user)):
    """Sync the authenticated Firebase user into the SQLite database."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (user['uid'],))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE firebase_uid = ?", (user['uid'],))
    else:
        cursor.execute(
            "INSERT INTO users (firebase_uid, email, last_login) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (user['uid'], user.get('email', ''))
        )
    conn.commit()
    conn.close()
    
    return {"status": "ok", "uid": user['uid']}

@app.get("/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    """Return the user's role from SQLite."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (user['uid'],))
    db_user = cursor.fetchone()
    conn.close()
    
    if db_user:
        return dict(db_user)
    return {"firebase_uid": user['uid'], "role": "user", "email": user.get('email', '')}

@app.get("/admin/users")
def get_users(user: dict = Depends(get_current_user)):
    """Admin only: list all users."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE firebase_uid = ?", (user['uid'],))
    me = cursor.fetchone()
    
    if not me or me['role'] != 'admin':
        conn.close()
        raise HTTPException(status_code=403, detail="Admin access required")
        
    cursor.execute("SELECT firebase_uid, email, role, created_at, last_login FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"users": users}

# --------------------------------------------------
# PERMANENT DEPOTS
# --------------------------------------------------

class DepotRequest(BaseModel):
    name: str
    latitude: float
    longitude: float

@app.get("/depots")
def get_depots(user: dict = Depends(get_current_user)):
    """Get permanent depots for the current user."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM depots WHERE user_id = ?", (user['uid'],))
    depots = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"depots": depots}

@app.post("/depots")
def add_depot(request: DepotRequest, user: dict = Depends(get_current_user)):
    """Add a permanent depot for the user."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO depots (user_id, name, latitude, longitude) VALUES (?, ?, ?, ?)",
        (user['uid'], request.name, request.latitude, request.longitude)
    )
    conn.commit()
    new_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM depots WHERE id = ?", (new_id,))
    depot = dict(cursor.fetchone())
    conn.close()
    
    return depot

@app.delete("/depots/{depot_id}")
def delete_depot(depot_id: int, user: dict = Depends(get_current_user)):
    """Delete a user's permanent depot."""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT user_id FROM depots WHERE id = ?", (depot_id,))
    depot = cursor.fetchone()
    if not depot or depot['user_id'] != user['uid']:
        conn.close()
        raise HTTPException(status_code=404, detail="Depot not found")
        
    cursor.execute("DELETE FROM depots WHERE id = ?", (depot_id,))
    conn.commit()
    conn.close()
    
    return {"status": "ok"}

