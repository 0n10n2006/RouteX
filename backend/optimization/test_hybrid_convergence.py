"""
REAL OSM: HYBRID QPSO CONVERGENCE EXPERIMENT

Tests the production Adaptive Hybrid QPSO + 2-opt optimizer
on the larger real OSM road network.

Experimental only.
Does NOT modify production optimizer code.

Setup:
- Real larger_area.osm
- 30 customers
- 20 particles
- beta = 0.5
- seeds = 1-10
- iterations = 50, 100, 200, 300

Measures:
- best travel time / fitness
- route distance
- runtime
- feasibility
- local search count
"""

import random
import time
from pathlib import Path

from backend.optimization.hybrid import hybrid_qpso
from backend.optimization.fitness import calculate_metrics
from backend.optimization.test_moqpso_larger_area import create_osm_problem
from traffic.osm_loader import load_road_network, prepare_graph


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

CUSTOMERS = 30
PARTICLES = 20
BETA = 0.5
SEEDS = range(1, 11)

ITERATION_BUDGETS = [50, 100, 200, 300]


# ============================================================
# PROBLEM SETUP
# ============================================================

def create_problem():
    """
    Load the exact larger-area OSM problem used by the
    previous MOQPSO vs Hybrid experiments.
    """

    project_root = Path(__file__).resolve().parents[2]

    osm_file = (
        project_root
        / "data"
        / "raw"
        / "larger_area.osm"
    )

    print(f"Loading OSM road network: {osm_file}")

    graph = prepare_graph(
        load_road_network(osm_file)
    )

    print(f"OSM nodes: {graph.number_of_nodes()}")
    print(f"OSM edges: {graph.number_of_edges()}")

    problem = create_osm_problem(
        graph,
        CUSTOMERS
    )

    total_demand = sum(
        customer["demand"]
        for customer in problem.customers
    )

    print(f"Total demand    : {total_demand}")

    vehicle_capacity = max(
        vehicle["capacity"]
        for vehicle in problem.vehicles
    )

    print(f"Vehicle capacity: {vehicle_capacity}")

    return problem


# ============================================================
# FITNESS / METRICS
# ============================================================

def evaluate_result(problem, result):
    """
    Extract travel time, distance and basic validity
    from the production Hybrid result.
    """

    if not result:
        return None

    routes = result.get("routes")

    if not routes:
        return None

    try:
        metrics = calculate_metrics(
            routes,
            problem
        )

        travel_time = metrics.get(
            "travel_time",
            result.get("fitness")
        )

        distance = metrics.get(
            "distance"
        )

    except Exception:
        travel_time = result.get("fitness")
        distance = None

    return {
        "routes": routes,
        "travel_time": travel_time,
        "distance": distance,
        "fitness": result.get("fitness"),
        "local_search_count": result.get(
            "local_search_count",
            0
        ),
        "feasible": True,
    }
# ============================================================
# SINGLE RUN
# ============================================================

def run_single(problem, seed, iterations):
    """
    Run production Hybrid QPSO + 2-opt once.
    """

    random.seed(seed)

    start = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=PARTICLES,
        iterations=iterations,
        beta=BETA,
    )

    runtime = time.perf_counter() - start

    evaluated = evaluate_result(
        problem,
        result
    )

    if evaluated is None:
        return {
            "seed": seed,
            "travel_time": None,
            "distance": None,
            "runtime": runtime,
            "local_search_count": 0,
            "feasible": False,
            "routes": None,
        }

    evaluated["seed"] = seed
    evaluated["runtime"] = runtime

    return evaluated


# ============================================================
# BENCHMARK
# ============================================================

def run_benchmark(problem, iterations):
    """
    Run seeds 1-10 for one iteration budget.
    """

    print()
    print("=" * 78)
    print(f"HYBRID QPSO CONVERGENCE - {iterations} ITERATIONS")
    print("=" * 78)

    results = []

    for seed in SEEDS:

        result = run_single(
            problem,
            seed,
            iterations
        )

        results.append(result)

        if result["travel_time"] is None:
            print(
                f"Seed {seed:2d}: INVALID "
                f"runtime={result['runtime']:.4f}s"
            )
            continue

        print(
            f"Seed {seed:2d}: "
            f"Time={result['travel_time']:.1f}/"
            f"{result['distance']:.1f}, "
            f"fitness={result['fitness']:.1f}, "
            f"2-opt={result['local_search_count']}, "
            f"feasible={result['feasible']}, "
            f"runtime={result['runtime']:.4f}s"
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def summarize(results, iterations):
    """
    Calculate aggregate statistics.
    """

    valid_results = [
        r for r in results
        if r["travel_time"] is not None
    ]

    if not valid_results:
        return {
            "iterations": iterations,
            "avg_time": None,
            "avg_distance": None,
            "avg_runtime": None,
            "avg_2opt": None,
            "feasible": 0,
            "count": 0,
        }

    avg_time = sum(
        r["travel_time"]
        for r in valid_results
    ) / len(valid_results)

    avg_distance = sum(
        r["distance"]
        for r in valid_results
    ) / len(valid_results)

    avg_runtime = sum(
        r["runtime"]
        for r in valid_results
    ) / len(valid_results)

    avg_2opt = sum(
        r["local_search_count"]
        for r in valid_results
    ) / len(valid_results)

    feasible = sum(
        1
        for r in valid_results
        if r["feasible"]
    )

    return {
        "iterations": iterations,
        "avg_time": avg_time,
        "avg_distance": avg_distance,
        "avg_runtime": avg_runtime,
        "avg_2opt": avg_2opt,
        "feasible": feasible,
        "count": len(valid_results),
    }


# ============================================================
# BEST / MOST INTERESTING RUN
# ============================================================

def print_best_run(results, iterations):
    """
    Print the best Hybrid run for this iteration budget.
    """

    valid_results = [
        r for r in results
        if r["travel_time"] is not None
    ]

    if not valid_results:
        return

    best = min(
        valid_results,
        key=lambda r: r["travel_time"]
    )

    print()
    print("-" * 78)
    print(f"BEST RUN - {iterations} ITERATIONS")
    print("-" * 78)

    print(f"Seed       : {best['seed']}")
    print(f"Travel time: {best['travel_time']:.2f}")
    print(f"Distance   : {best['distance']:.2f}")
    print(f"Fitness    : {best['fitness']:.2f}")
    print(f"2-opt calls: {best['local_search_count']}")
    print(f"Runtime    : {best['runtime']:.4f}s")
    print(f"Feasible   : {best['feasible']}")

    print("Routes:")
    for route in best["routes"]:
        print(f"  {route}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("# REAL OSM: HYBRID QPSO CONVERGENCE EXPERIMENT")
    print()
    print("Problem source: existing larger-area MOQPSO vs Hybrid benchmark")
    print(f"Customers  : {CUSTOMERS}")
    print(f"Particles  : {PARTICLES}")
    print(f"Beta       : {BETA}")
    print("Seeds      : 1-10")
    print(f"Iterations : {ITERATION_BUDGETS}")

    # IMPORTANT:
    # Build the problem ONCE so every iteration budget
    # uses the exact same customers, demands and road matrix.
    problem = create_problem()

    all_results = {}
    summaries = []

    for iterations in ITERATION_BUDGETS:

        results = run_benchmark(
            problem,
            iterations
        )

        all_results[iterations] = results

        summary = summarize(
            results,
            iterations
        )

        summaries.append(summary)

        print_best_run(
            results,
            iterations
        )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 100)
    print("HYBRID QPSO CONVERGENCE SUMMARY")
    print("=" * 100)

    print()
    print(
        "## Iterations | Avg Best Time | Avg Best Dist | "
        "Avg Runtime | Avg 2-opt | Feasible"
    )

    for summary in summaries:

        if summary["avg_time"] is None:
            print(
                f"{summary['iterations']:8d} | "
                f"{'INVALID':>14} | "
                f"{'INVALID':>14} | "
                f"{'INVALID':>11} | "
                f"{'INVALID':>9} | "
                f"{summary['feasible']}/10"
            )
            continue

        print(
            f"{summary['iterations']:8d} | "
            f"{summary['avg_time']:14.2f} | "
            f"{summary['avg_distance']:14.2f} | "
            f"{summary['avg_runtime']:10.4f}s | "
            f"{summary['avg_2opt']:9.2f} | "
            f"{summary['feasible']}/10"
        )

    # ========================================================
    # IMPROVEMENT ANALYSIS
    # ========================================================

    print()
    print("=" * 78)
    print("CONVERGENCE IMPROVEMENT")
    print("=" * 78)

    baseline = summaries[0]

    if baseline["avg_time"] is not None:

        for summary in summaries[1:]:

            if summary["avg_time"] is None:
                continue

            time_improvement = (
                (
                    baseline["avg_time"]
                    - summary["avg_time"]
                )
                / baseline["avg_time"]
            ) * 100

            distance_improvement = (
                (
                    baseline["avg_distance"]
                    - summary["avg_distance"]
                )
                / baseline["avg_distance"]
            ) * 100

            print(
                f"{baseline['iterations']} -> "
                f"{summary['iterations']} iterations: "
                f"time improvement="
                f"{time_improvement:.2f}%, "
                f"distance improvement="
                f"{distance_improvement:.2f}%"
            )

    # ========================================================
    # MARGINAL IMPROVEMENT
    # ========================================================

    print()
    print("=" * 78)
    print("MARGINAL IMPROVEMENT BETWEEN ITERATION BUDGETS")
    print("=" * 78)

    for previous, current in zip(
        summaries,
        summaries[1:]
    ):

        if (
            previous["avg_time"] is None
            or current["avg_time"] is None
        ):
            continue

        time_change = (
            (
                previous["avg_time"]
                - current["avg_time"]
            )
            / previous["avg_time"]
        ) * 100

        distance_change = (
            (
                previous["avg_distance"]
                - current["avg_distance"]
            )
            / previous["avg_distance"]
        ) * 100

        print(
            f"{previous['iterations']} -> "
            f"{current['iterations']}: "
            f"time={time_change:.3f}%, "
            f"distance={distance_change:.3f}%"
        )

    # ========================================================
    # BEST OVERALL RUN
    # ========================================================

    print()
    print("=" * 78)
    print("BEST OVERALL HYBRID RUN")
    print("=" * 78)

    all_valid = []

    for results in all_results.values():
        all_valid.extend(
            r for r in results
            if r["travel_time"] is not None
        )

    if all_valid:

        best = min(
            all_valid,
            key=lambda r: r["travel_time"]
        )

        print(f"Seed       : {best['seed']}")
        print(f"Travel time: {best['travel_time']:.2f}")
        print(f"Distance   : {best['distance']:.2f}")
        print(f"Fitness    : {best['fitness']:.2f}")
        print(f"2-opt calls: {best['local_search_count']}")
        print(f"Runtime    : {best['runtime']:.4f}s")
        print(f"Feasible   : {best['feasible']}")

        print("Routes:")
        for route in best["routes"]:
            print(f"  {route}")

    print()
    print("=" * 78)
    print("EXPERIMENT COMPLETE")
    print("=" * 78)


if __name__ == "__main__":
    main()