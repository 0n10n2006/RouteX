# Benchmark Metrics



def create_result(
    scenario_id,
    algorithm,
    travel_time,
    distance,
    congestion_penalty,
    fuel_cost,
    constraint_violations,
    runtime,
    iterations,
    best_fitness
):

    result = {
        "scenario_id": scenario_id,
        "algorithm": algorithm,
        "travel_time": travel_time,
        "distance": distance,
        "congestion_penalty": congestion_penalty,
        "fuel_cost": fuel_cost,
        "constraint_violations": constraint_violations,
        "runtime": runtime,
        "iterations": iterations,
        "best_fitness": best_fitness
    }

    return result

