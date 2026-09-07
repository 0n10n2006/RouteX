import random
import time

from backend.optimization.traffic_scenarios import (
    create_kothrud_problem,
    create_kothrud_problem_with_incident,
    resolve_kothrud_incident,
    KOTHRUD_TRAFFIC_FACTORS,
    KOTHRUD_INCIDENT_SCENARIOS,
)

from backend.optimization.hybrid import hybrid_qpso
from backend.optimization.fitness import calculate_metrics

from traffic.graph_builder import build_route_matrix
from traffic.osm_loader import load_road_network, prepare_graph


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

SEEDS = [1, 2, 3, 4, 5]

# Existing verified incident edges
SINGLE_INCIDENT = (4704828557, 4704828553, 0)

MULTIPLE_INCIDENTS = [
    (4704828557, 4704828553, 0),
    (2199397321, 2199397323, 0),
]

INCIDENT_FACTOR = 0.1


# ---------------------------------------------------------
# RUN HYBRID QPSO
# ---------------------------------------------------------

def run_hybrid(problem, seed):
    """Run Hybrid QPSO and measure runtime."""

    random.seed(seed)

    start_time = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=10,
        iterations=20,
        beta=0.5,
    )

    runtime = time.perf_counter() - start_time

    metrics = calculate_metrics(
        result["routes"],
        problem
    )

    return {
        "routes": result["routes"],
        "fitness": result["fitness"],
        "distance": metrics["distance"],
        "travel_time": metrics.get("travel_time"),
        "runtime": runtime,
    }


# ---------------------------------------------------------
# BUILD PEAK TRAFFIC PROBLEM
# ---------------------------------------------------------

def create_peak_problem():
    """
    Create the same Kothrud road problem but with stronger
    simulated traffic slowdown.

    The existing Kothrud traffic factors are multiplied by
    an additional peak factor.
    """

    graph = prepare_graph(
        load_road_network(
            create_kothrud_problem.__globals__["KOTHRUD_OSM_FILE"]
        )
    )

    # Existing locations from the normal Kothrud problem
    normal_problem = create_kothrud_problem()
    locations = normal_problem.metadata["locations"]

    peak_factors = {
        road_type: factor * 0.70
        for road_type, factor in KOTHRUD_TRAFFIC_FACTORS.items()
    }

    matrix_data = build_route_matrix(
        graph,
        locations,
        traffic_factors=peak_factors,
    )

    # Keep the same vehicles and customers
    from backend.optimization.problem import ProblemInstance

    return ProblemInstance(
        distance_matrix=matrix_data["distance_matrix"],
        travel_time_matrix=matrix_data["travel_time_matrix"],
        vehicles=normal_problem.vehicles,
        customers=normal_problem.customers,
        metadata={
            **matrix_data["metadata"],
            "source": "Kothrud OSM extract with simulated peak traffic",
            "traffic_factors": peak_factors,
            "scenario": "peak_traffic",
            "locations": locations,
        },
    )


# ---------------------------------------------------------
# PRINT RESULT
# ---------------------------------------------------------

def print_result(name, result):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print("Routes       :", result["routes"])
    print("Fitness      :", round(result["fitness"], 2))
    print("Distance     :", round(result["distance"], 2))

    if result["travel_time"] is not None:
        print("Travel Time  :", round(result["travel_time"], 2))

    print("Runtime      :", round(result["runtime"], 6), "seconds")


# ---------------------------------------------------------
# MAIN EXPERIMENT
# ---------------------------------------------------------

def main():

    print("\nWEEK 5 - DYNAMIC TRAFFIC & INCIDENT EXPERIMENTS")
    print("=" * 60)

    # -----------------------------------------------------
    # 1. NORMAL TRAFFIC
    # -----------------------------------------------------

    print("\nCreating NORMAL traffic problem...")

    normal_problem = create_kothrud_problem()

    normal_results = []

    for seed in SEEDS:
        result = run_hybrid(normal_problem, seed)
        normal_results.append(result)

    normal_result = {
        "routes": normal_results[0]["routes"],
        "fitness": sum(r["fitness"] for r in normal_results) / len(normal_results),
        "distance": sum(r["distance"] for r in normal_results) / len(normal_results),
        "travel_time": sum(r["travel_time"] for r in normal_results) / len(normal_results),
        "runtime": sum(r["runtime"] for r in normal_results) / len(normal_results),
    }

    print_result(
        "1. NORMAL TRAFFIC",
        normal_result
    )

    # -----------------------------------------------------
    # 2. PEAK TRAFFIC
    # -----------------------------------------------------

    print("\nCreating PEAK traffic problem...")

    peak_problem = create_peak_problem()

    peak_results = []

    for seed in SEEDS:
        result = run_hybrid(peak_problem, seed)
        peak_results.append(result)

    peak_result = {
        "routes": peak_results[0]["routes"],
        "fitness": sum(r["fitness"] for r in peak_results) / len(peak_results),
        "distance": sum(r["distance"] for r in peak_results) / len(peak_results),
        "travel_time": sum(r["travel_time"] for r in peak_results) / len(peak_results),
        "runtime": sum(r["runtime"] for r in peak_results) / len(peak_results),
    }

    print_result(
        "2. PEAK TRAFFIC",
        peak_result
    )

    # -----------------------------------------------------
    # 3. SINGLE ROAD INCIDENT
    # -----------------------------------------------------

    print("\nCreating SINGLE INCIDENT problem...")

    single_incident_problem = create_kothrud_problem_with_incident(
        SINGLE_INCIDENT,
        incident_factor=INCIDENT_FACTOR,
        incident_scenario="single_incident",
        incident_description="Simulated slowdown on one Kothrud road",
    )

    single_results = []

    for seed in SEEDS:
        result = run_hybrid(single_incident_problem, seed)
        single_results.append(result)

    single_result = {
        "routes": single_results[0]["routes"],
        "fitness": sum(r["fitness"] for r in single_results) / len(single_results),
        "distance": sum(r["distance"] for r in single_results) / len(single_results),
        "travel_time": sum(r["travel_time"] for r in single_results) / len(single_results),
        "runtime": sum(r["runtime"] for r in single_results) / len(single_results),
    }

    print_result(
        "3. SINGLE ROAD INCIDENT",
        single_result
    )

    # -----------------------------------------------------
    # 4. MULTIPLE ROAD INCIDENTS
    # -----------------------------------------------------

    print("\nCreating MULTIPLE INCIDENT problem...")

    graph = prepare_graph(
        load_road_network(
            create_kothrud_problem.__globals__["KOTHRUD_OSM_FILE"]
        )
    )

    locations = normal_problem.metadata["locations"]

    matrix_data = build_route_matrix(
        graph,
        locations,
        traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
        incident_edges={
            edge: INCIDENT_FACTOR
            for edge in MULTIPLE_INCIDENTS
        },
    )

    from backend.optimization.problem import ProblemInstance

    multiple_incident_problem = ProblemInstance(
        distance_matrix=matrix_data["distance_matrix"],
        travel_time_matrix=matrix_data["travel_time_matrix"],
        vehicles=normal_problem.vehicles,
        customers=normal_problem.customers,
        metadata={
            **matrix_data["metadata"],
            "source": "Kothrud OSM extract with multiple simulated incidents",
            "traffic_factors": KOTHRUD_TRAFFIC_FACTORS,
            "scenario": "multiple_incidents",
            "incident_edges": [
                list(edge)
                for edge in MULTIPLE_INCIDENTS
            ],
            "locations": locations,
        },
    )

    multiple_results = []

    for seed in SEEDS:
        result = run_hybrid(multiple_incident_problem, seed)
        multiple_results.append(result)

    multiple_result = {
        "routes": multiple_results[0]["routes"],
        "fitness": sum(r["fitness"] for r in multiple_results) / len(multiple_results),
        "distance": sum(r["distance"] for r in multiple_results) / len(multiple_results),
        "travel_time": sum(r["travel_time"] for r in multiple_results) / len(multiple_results),
        "runtime": sum(r["runtime"] for r in multiple_results) / len(multiple_results),
    }

    print_result(
        "4. MULTIPLE ROAD INCIDENTS",
        multiple_result
    )

    # -----------------------------------------------------
    # 5. REROUTING ANALYSIS
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("REROUTING ANALYSIS")
    print("=" * 60)

    print(
        "Normal -> Single Incident route changed:",
        normal_result["routes"] != single_result["routes"]
    )

    print(
        "Normal -> Multiple Incident route changed:",
        normal_result["routes"] != multiple_result["routes"]
    )

    print(
        "Normal -> Peak route changed:",
        normal_result["routes"] != peak_result["routes"]
    )

    # -----------------------------------------------------
    # 6. TRAVEL TIME CHANGES
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("TRAVEL TIME CHANGE")
    print("=" * 60)

    normal_time = normal_result["travel_time"]

    scenarios = [
        ("Peak Traffic", peak_result),
        ("Single Incident", single_result),
        ("Multiple Incidents", multiple_result),
    ]

    for name, result in scenarios:

        new_time = result["travel_time"]

        if normal_time and normal_time != 0:
            change = (
                (new_time - normal_time)
                / normal_time
            ) * 100
        else:
            change = 0

        print(
            f"{name}: "
            f"{normal_time:.2f} -> {new_time:.2f} "
            f"({change:+.2f}%)"
        )


if __name__ == "__main__":
    main()