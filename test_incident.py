from backend.optimization.traffic_scenarios import (
    create_kothrud_problem,
)

from traffic.graph_builder import build_route_matrix
from backend.optimization.traffic_scenarios import (
    prepare_graph,
    load_road_network,
    KOTHRUD_OSM_FILE,
    KOTHRUD_TRAFFIC_FACTORS,
    _connected_locations,
)

import networkx as nx


graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))
locations = _connected_locations(graph)

# This edge is unique to the first 0 -> 1 corridor.
incident_edge = (4704828557, 4704828553, 0)

normal = build_route_matrix(
    graph,
    locations,
    traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
)

incident = build_route_matrix(
    graph,
    locations,
    traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
    incident_edges={
        incident_edge: 0.1
    },
)

print("NORMAL 0 -> 1:", round(normal["travel_time_matrix"][0][1], 2))
print("INCIDENT 0 -> 1:", round(incident["travel_time_matrix"][0][1], 2))

print()

print("NORMAL 0 -> 2:", round(normal["travel_time_matrix"][0][2], 2))
print("INCIDENT 0 -> 2:", round(incident["travel_time_matrix"][0][2], 2))

print()

print("NORMAL 0 -> 3:", round(normal["travel_time_matrix"][0][3], 2))
print("INCIDENT 0 -> 3:", round(incident["travel_time_matrix"][0][3], 2))

print()

print("NORMAL 0 -> 4:", round(normal["travel_time_matrix"][0][4], 2))
print("INCIDENT 0 -> 4:", round(incident["travel_time_matrix"][0][4], 2))