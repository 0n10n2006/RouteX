"""
RouteX - Week 5 Dynamic Re-routing Experiment

Evaluation-only script.

Purpose:
    Verify that a simulated road incident changes the travel-time
    landscape and causes Hybrid QPSO + 2-opt to dynamically re-optimize.

Experiment:
    Normal Kothrud
        ->
    Hybrid QPSO + 2-opt
        ->
    Route A
        ->
    Simulated incident on a specific OSM edge
        ->
    Updated travel-time matrix
        ->
    Hybrid QPSO + 2-opt
        ->
    Route B

The same random seed is used for the normal and incident runs.

This file does NOT modify:
    - QPSO
    - Hybrid QPSO
    - traffic modules
    - API
    - database
"""


import random
import sys
from pathlib import Path


# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------

from backend.optimization.hybrid import hybrid_qpso
from backend.optimization.problem import ProblemInstance
from backend.optimization import traffic_scenarios
from traffic.graph_builder import build_route_matrix


# ---------------------------------------------------------------------
# Experiment configuration
# ---------------------------------------------------------------------

SEEDS = [42, 43, 44, 45, 46]

# Verified Kothrud edge that has an alternative corridor.
INCIDENT_EDGE = (
    4704828557,
    4704828553,
    0,
)

# 10% of normal speed.
INCIDENT_FACTOR = 0.10


# ---------------------------------------------------------------------
# Problem construction
# ---------------------------------------------------------------------

def build_problems():
    """
    Build the normal and incident Kothrud problems.

    Uses the same graph construction as traffic_scenarios.py,
    but directly supplies the verified incident edge to
    build_route_matrix().
    """

    # The existing Kothrud scenario already contains the exact graph
    # construction we need. We reproduce it here without modifying
    # that module.

    graph = traffic_scenarios.load_road_network(
        traffic_scenarios.KOTHRUD_OSM_FILE
    )

    graph = traffic_scenarios.prepare_graph(graph)

    locations = traffic_scenarios._connected_locations(graph)

    vehicles = [
        {"id": 1, "capacity": 7},
        {"id": 2, "capacity": 7},
    ]

    customers = [
        {"id": 1, "demand": 2},
        {"id": 2, "demand": 3},
        {"id": 3, "demand": 2},
        {"id": 4, "demand": 3},
    ]

    # -------------------------------------------------------------
    # Normal traffic
    # -------------------------------------------------------------

    normal_matrix = build_route_matrix(
        graph,
        locations,
        traffic_factors=traffic_scenarios.KOTHRUD_TRAFFIC_FACTORS,
        incident_edges=None,
    )

    normal_problem = ProblemInstance(
        distance_matrix=normal_matrix["distance_matrix"],
        travel_time_matrix=normal_matrix["travel_time_matrix"],
        vehicles=vehicles,
        customers=customers,
        metadata={
            **normal_matrix["metadata"],
            "source": "Kothrud OSM extract with simulated traffic",
            "traffic_factors": traffic_scenarios.KOTHRUD_TRAFFIC_FACTORS,
        },
    )

    # -------------------------------------------------------------
    # Incident traffic
    # -------------------------------------------------------------

    incident_matrix = build_route_matrix(
        graph,
        locations,
        traffic_factors=traffic_scenarios.KOTHRUD_TRAFFIC_FACTORS,
        incident_edges={
            INCIDENT_EDGE: INCIDENT_FACTOR
        },
    )

    incident_problem = ProblemInstance(
        distance_matrix=incident_matrix["distance_matrix"],
        travel_time_matrix=incident_matrix["travel_time_matrix"],
        vehicles=vehicles,
        customers=customers,
        metadata={
            **incident_matrix["metadata"],
            "source": "Kothrud OSM extract with simulated traffic",
            "traffic_factors": traffic_scenarios.KOTHRUD_TRAFFIC_FACTORS,
            "incident": {
                "type": "simulated road-speed incident",
                "edge": list(INCIDENT_EDGE),
                "speed_factor": INCIDENT_FACTOR,
            },
        },
    )

    return normal_problem, incident_problem


# ---------------------------------------------------------------------
# Single experiment
# ---------------------------------------------------------------------

def run_single_experiment(seed):
    """
    Run normal and incident optimization using the same seed.
    """

    normal_problem, incident_problem = build_problems()

    # Normal condition
    random.seed(seed)

    before = hybrid_qpso(normal_problem)

    # Incident condition
    random.seed(seed)

    after = hybrid_qpso(incident_problem)

    before_routes = before["routes"]
    after_routes = after["routes"]

    before_fitness = before["fitness"]
    after_fitness = after["fitness"]

    route_changed = before_routes != after_routes

    if before_fitness != 0:
        fitness_change = (
            (after_fitness - before_fitness)
            / before_fitness
        ) * 100
    else:
        fitness_change = 0.0

    return {
        "seed": seed,
        "before_routes": before_routes,
        "after_routes": after_routes,
        "before_fitness": before_fitness,
        "after_fitness": after_fitness,
        "fitness_change": fitness_change,
        "route_changed": route_changed,
    }


# ---------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------

def main():

    print()
    print("=" * 72)
    print("RouteX - Week 5 Dynamic Re-routing Experiment")
    print("=" * 72)

    print(f"Scenario        : Kothrud")
    print(f"Incident edge   : {INCIDENT_EDGE}")
    print(f"Incident factor : {INCIDENT_FACTOR}")
    print(f"Seeds           : {SEEDS}")
    print()

    # -------------------------------------------------------------
    # Verify incident changes travel-time matrix
    # -------------------------------------------------------------

    normal_problem, incident_problem = build_problems()

    normal_tt = normal_problem.travel_time_matrix
    incident_tt = incident_problem.travel_time_matrix

    changed_entries = 0
    maximum_change = 0.0

    for i in range(len(normal_tt)):
        for j in range(len(normal_tt[i])):

            difference = abs(
                incident_tt[i][j] - normal_tt[i][j]
            )

            if difference > 1e-9:
                changed_entries += 1
                maximum_change = max(
                    maximum_change,
                    difference,
                )

    print("Travel-time matrix verification")
    print("-" * 72)
    print(f"Changed entries : {changed_entries}")
    print(f"Maximum change  : {maximum_change:.4f}")
    print()

    if changed_entries == 0:
        print("ERROR: Incident did not change the travel-time matrix.")
        print("Experiment stopped.")
        return

    # -------------------------------------------------------------
    # Run seeds
    # -------------------------------------------------------------

    results = []

    for seed in SEEDS:

        print("-" * 72)
        print(f"Running seed {seed}")
        print("-" * 72)

        result = run_single_experiment(seed)

        results.append(result)

        print(f"Before route    : {result['before_routes']}")
        print(f"After route     : {result['after_routes']}")

        print(
            f"Before fitness  : "
            f"{result['before_fitness']:.4f}"
        )

        print(
            f"After fitness   : "
            f"{result['after_fitness']:.4f}"
        )

        print(
            f"Fitness change  : "
            f"{result['fitness_change']:+.2f}%"
        )

        print(
            f"Route changed   : "
            f"{'YES' if result['route_changed'] else 'NO'}"
        )

        print()

    # -------------------------------------------------------------
    # Aggregate results
    # -------------------------------------------------------------

    changed_count = sum(
        1
        for result in results
        if result["route_changed"]
    )

    route_change_rate = (
        changed_count / len(results)
    ) * 100

    average_before = sum(
        result["before_fitness"]
        for result in results
    ) / len(results)

    average_after = sum(
        result["after_fitness"]
        for result in results
    ) / len(results)

    if average_before != 0:
        average_change = (
            (average_after - average_before)
            / average_before
        ) * 100
    else:
        average_change = 0.0

    # -------------------------------------------------------------
    # Results
    # -------------------------------------------------------------

    print()
    print("=" * 72)
    print("WEEK 5 RESULTS")
    print("=" * 72)

    print(f"Runs                     : {len(results)}")

    print(
        f"Routes changed           : "
        f"{changed_count}/{len(results)}"
    )

    print(
        f"Route-change rate        : "
        f"{route_change_rate:.2f}%"
    )

    print(
        f"Average before fitness   : "
        f"{average_before:.4f}"
    )

    print(
        f"Average after fitness    : "
        f"{average_after:.4f}"
    )

    print(
        f"Average fitness change   : "
        f"{average_change:+.2f}%"
    )

    print("=" * 72)

    if changed_count > 0:

        print("RESULT: Dynamic re-routing was observed.")

        print(
            f"Hybrid QPSO changed the route assignment "
            f"in {changed_count}/{len(results)} runs."
        )

        print(
            "The simulated incident changed the "
            "travel-time landscape and triggered "
            "re-optimization."
        )

    else:

        print("RESULT: No route changes were observed.")

        print(
            "The incident changed travel-time costs, "
            "but the optimizer selected the same "
            "route assignment in all tested runs."
        )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()