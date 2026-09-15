import csv
import random
import time
import math
from pathlib import Path

from backend.optimization.problem import ProblemInstance
from backend.optimization.hybrid import hybrid_qpso
from backend.optimization.fitness import fitness
from backend.optimization.constraints import validate


# ==========================================================
# EXPERIMENT SETTINGS
# ==========================================================

NUM_SEEDS = 10

LOCAL_SEARCH_PROBABILITIES = [
    0.00,
    0.25,
    0.50,
    0.75,
    1.00
]

# IMPORTANT:
# These values are kept fixed because beta,
# population and iterations have already been tuned.
NUM_PARTICLES = 20
ITERATIONS = 50
BETA = 0.5


# ==========================================================
# SCENARIOS
# ==========================================================

scenarios = [
    {
        "id": "S1",
        "demand": "Low",
        "traffic": "Low",
        "incident": False,
        "vehicles": 3,
        "delivery_points": 10
    },
    {
        "id": "S2",
        "demand": "Medium",
        "traffic": "Medium",
        "incident": False,
        "vehicles": 5,
        "delivery_points": 15
    },
    {
        "id": "S3",
        "demand": "High",
        "traffic": "High",
        "incident": False,
        "vehicles": 10,
        "delivery_points": 25
    },
    {
        "id": "S4",
        "demand": "Medium",
        "traffic": "High",
        "incident": True,
        "vehicles": 5,
        "delivery_points": 15
    },
    {
        "id": "S5",
        "demand": "High",
        "traffic": "High",
        "incident": True,
        "vehicles": 10,
        "delivery_points": 25
    },
    {
        "id": "S6",
        "demand": "High",
        "traffic": "High",
        "incident": "multiple",
        "vehicles": 10,
        "delivery_points": 25
    }
]


# ==========================================================
# DISTANCE MATRIX
# ==========================================================

def create_distance_matrix(
    num_points,
    traffic,
    incident,
    seed
):

    random.seed(seed)

    coordinates = []

    for _ in range(num_points):

        x = random.randint(0, 100)
        y = random.randint(0, 100)

        coordinates.append((x, y))

    traffic_factor = {
        "Low": 1.0,
        "Medium": 1.2,
        "High": 1.5
    }

    factor = traffic_factor[traffic]

    matrix = []

    for i in range(num_points):

        row = []

        for j in range(num_points):

            if i == j:
                row.append(0)
                continue

            x1, y1 = coordinates[i]
            x2, y2 = coordinates[j]

            distance = math.sqrt(
                (x1 - x2) ** 2
                + (y1 - y2) ** 2
            )

            distance *= factor

            # Single incident
            if incident is True:

                if (i + j) % 5 == 0:
                    distance *= 1.8

            # Multiple incidents
            elif incident == "multiple":

                if (i + j) % 5 == 0:
                    distance *= 1.8

                if (i * j) % 7 == 0:
                    distance *= 1.6

                if abs(i - j) == 3:
                    distance *= 1.5

            row.append(round(distance, 2))

        matrix.append(row)

    return matrix


# ==========================================================
# CREATE PROBLEM
# ==========================================================

def create_problem(
    scenario,
    seed
):

    num_customers = scenario["delivery_points"]

    distance_matrix = create_distance_matrix(
        num_customers + 1,
        scenario["traffic"],
        scenario["incident"],
        seed
    )

    demand_range = {
        "Low": (1, 2),
        "Medium": (2, 4),
        "High": (3, 6)
    }

    low, high = demand_range[
        scenario["demand"]
    ]

    random.seed(seed + 1000)

    customers = []

    for customer_id in range(
        1,
        num_customers + 1
    ):

        customers.append({
            "id": customer_id,
            "demand": random.randint(
                low,
                high
            )
        })

    if scenario["demand"] == "Low":
        capacity = 15

    elif scenario["demand"] == "Medium":
        capacity = 20

    else:
        capacity = 25

    vehicles = []

    for vehicle_id in range(
        1,
        scenario["vehicles"] + 1
    ):

        vehicles.append({
            "id": vehicle_id,
            "capacity": capacity
        })

    return ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers,
        metadata={
            "scenario_id": scenario["id"],
            "demand": scenario["demand"],
            "traffic": scenario["traffic"],
            "incident": scenario["incident"]
        }
    )


# ==========================================================
# RUN ONE HYBRID EXPERIMENT
# ==========================================================

def run_hybrid(
    problem,
    local_search_probability
):

    start_time = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=NUM_PARTICLES,
        iterations=ITERATIONS,
        beta=BETA,
        local_search_probability=local_search_probability
    )

    runtime = (
        time.perf_counter()
        - start_time
    )

    if result is None:

        return {
            "fitness": float("inf"),
            "runtime": runtime,
            "local_search_count": 0,
            "constraint_violations": 1
        }

    routes = result["routes"]

    if routes and validate(
        routes,
        problem
    ):

        score = fitness(
            routes,
            problem
        )

        return {
            "fitness": score,
            "runtime": runtime,
            "local_search_count":
                result["local_search_count"],
            "constraint_violations": 0
        }

    return {
        "fitness": float("inf"),
        "runtime": runtime,
        "local_search_count":
            result["local_search_count"],
        "constraint_violations": 1
    }


# ==========================================================
# MAIN EXPERIMENT
# ==========================================================

def main():

    results = []

    total_runs = (
        len(LOCAL_SEARCH_PROBABILITIES)
        * len(scenarios)
        * NUM_SEEDS
    )

    current_run = 0

    print(
        "=========================================="
    )

    print(
        "LOCAL SEARCH PROBABILITY TUNING"
    )

    print(
        "=========================================="
    )

    print(
        "Probabilities:",
        LOCAL_SEARCH_PROBABILITIES
    )

    print(
        "Scenarios:",
        len(scenarios)
    )

    print(
        "Seeds:",
        NUM_SEEDS
    )

    print(
        "Total experiments:",
        total_runs
    )

    print(
        "Fixed population:",
        NUM_PARTICLES
    )

    print(
        "Fixed iterations:",
        ITERATIONS
    )

    print(
        "Fixed beta:",
        BETA
    )

    for probability in LOCAL_SEARCH_PROBABILITIES:

        print(
            "\n########################################"
        )

        print(
            "Local Search Probability:",
            probability
        )

        print(
            "########################################"
        )

        for scenario in scenarios:

            print(
                f"\nScenario: {scenario['id']}"
            )

            for seed in range(
                1,
                NUM_SEEDS + 1
            ):

                problem = create_problem(
                    scenario,
                    seed
                )

                # Same seed for every probability
                # so the comparison is fair.
                random.seed(seed)

                current_run += 1

                result = run_hybrid(
                    problem,
                    probability
                )

                print(
                    f"[{current_run}/{total_runs}] "
                    f"P={probability:.2f} | "
                    f"{scenario['id']} | "
                    f"Seed {seed} | "
                    f"Fitness: "
                    f"{result['fitness']:.2f} | "
                    f"Runtime: "
                    f"{result['runtime']:.4f}s | "
                    f"LS Calls: "
                    f"{result['local_search_count']}"
                )

                results.append({
                    "local_search_probability":
                        probability,
                    "scenario_id":
                        scenario["id"],
                    "seed":
                        seed,
                    "fitness":
                        result["fitness"],
                    "runtime":
                        result["runtime"],
                    "iterations":
                        ITERATIONS,
                    "local_search_count":
                        result["local_search_count"],
                    "constraint_violations":
                        result["constraint_violations"]
                })


    # ======================================================
    # SAVE RESULTS
    # ======================================================

    output_directory = (
        Path(__file__).resolve().parent
        / "results"
    )

    output_directory.mkdir(
        exist_ok=True
    )

    output_file = (
        output_directory
        / "local_search_tuning.csv"
    )

    with open(
        output_file,
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "local_search_probability",
                "scenario_id",
                "seed",
                "fitness",
                "runtime",
                "iterations",
                "local_search_count",
                "constraint_violations"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print(
        "\n=========================================="
    )

    print(
        "LOCAL SEARCH TUNING COMPLETED"
    )

    print(
        "=========================================="
    )

    print(
        "Total experiments:",
        len(results)
    )

    print(
        "Results saved to:",
        output_file
    )


if __name__ == "__main__":
    main()
