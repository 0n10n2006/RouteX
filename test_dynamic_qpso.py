import random

from backend.optimization.traffic_scenarios import (
    create_kothrud_problem,
    prepare_graph,
    load_road_network,
    KOTHRUD_OSM_FILE,
    KOTHRUD_TRAFFIC_FACTORS,
    _connected_locations,
)

from traffic.graph_builder import build_route_matrix
from backend.optimization.hybrid import hybrid_qpso


# Build the real OSM graph.
graph = prepare_graph(
    load_road_network(KOTHRUD_OSM_FILE)
)

locations = _connected_locations(graph)

# This edge is unique to one of the two 0 -> 1 corridors.
incident_edge = (
    4704828557,
    4704828553,
    0,
)


# -------------------------
# NORMAL SCENARIO
# -------------------------

normal_matrix = build_route_matrix(
    graph,
    locations,
    traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
)

normal_problem = create_kothrud_problem()
normal_problem.travel_time_matrix = normal_matrix["travel_time_matrix"]

random.seed(42)

normal_result = hybrid_qpso(
    normal_problem
)


# -------------------------
# INCIDENT SCENARIO
# -------------------------

incident_matrix = build_route_matrix(
    graph,
    locations,
    traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
    incident_edges={
        incident_edge: 0.1
    },
)

incident_problem = create_kothrud_problem()
incident_problem.travel_time_matrix = incident_matrix["travel_time_matrix"]

random.seed(42)

incident_result = hybrid_qpso(
    incident_problem
)


# -------------------------
# RESULTS
# -------------------------

print("NORMAL")
print("Routes:", normal_result["routes"])
print("Fitness:", normal_result["fitness"])

print()

print("INCIDENT")
print("Routes:", incident_result["routes"])
print("Fitness:", incident_result["fitness"])

print()

print("ROUTE CHANGED:")
print(
    normal_result["routes"]
    != incident_result["routes"]
)

print()

print("FITNESS CHANGE:")
print(
    normal_result["fitness"],
    "->",
    incident_result["fitness"]
)