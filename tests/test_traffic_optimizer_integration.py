import math

from backend.optimization.fitness import calculate_metrics, fitness
from backend.optimization.greedy_vrp import greedy_vrp
from backend.optimization.traffic_scenarios import create_kothrud_problem
from backend.optimization.constraints import validate


def test_kothrud_osm_problem_runs_through_the_optimizer():
    problem = create_kothrud_problem()

    assert problem.metadata["source"] == "Kothrud OSM extract with simulated traffic"
    assert len(problem.distance_matrix) == 5
    assert len(problem.travel_time_matrix) == 5

    routes = greedy_vrp(problem)
    assert validate(routes, problem)

    metrics = calculate_metrics(routes, problem)
    assert math.isfinite(metrics["distance"])
    assert math.isfinite(metrics["travel_time"])
    assert fitness(routes, problem) == metrics["travel_time"]
