from backend.optimization.traffic_scenarios import (
    prepare_graph,
    load_road_network,
    KOTHRUD_OSM_FILE,
    KOTHRUD_TRAFFIC_FACTORS,
)

from traffic.graph_builder import _prepare_travel_times

graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))

u = 1563310394
v = 4704828557
key = 0

edge = graph[u][v][key]

print("EDGE:")
print(edge)

normal_graph = _prepare_travel_times(
    graph,
    KOTHRUD_TRAFFIC_FACTORS,
    None,
)

incident_graph = _prepare_travel_times(
    graph,
    KOTHRUD_TRAFFIC_FACTORS,
    {(u, v, key): 0.1},
)

print()
print("NORMAL:")
print(normal_graph[u][v][key]["travel_time"])

print()
print("WITH INCIDENT:")
print(incident_graph[u][v][key]["travel_time"])

print()
print("MULTIPLIER:")
print(
    incident_graph[u][v][key]["travel_time"]
    / normal_graph[u][v][key]["travel_time"]
)