"""Adapters that turn RouteX's OSM road graph into optimizer problems.

The Kothrud traffic values are simulated speed reductions applied to real OSM
road geometry. They are not live traffic measurements.
"""

from pathlib import Path

import networkx as nx

from traffic.graph_builder import build_route_matrix
from traffic.osm_loader import load_road_network, prepare_graph

from .problem import ProblemInstance


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KOTHRUD_OSM_FILE = PROJECT_ROOT / "data/raw/kothrud_test_area.osm"

# Speed multipliers in (0, 1]. Lower values mean slower simulated traffic.
KOTHRUD_TRAFFIC_FACTORS = {
    "primary": 0.65,
    "secondary": 0.75,
    "tertiary": 0.80,
    "residential": 0.70,
    "service": 0.70,
    "default": 0.75,
}


def _connected_locations(graph, count=5):
    """Select deterministic, geographically spread nodes in one SCC.

    Exact OSM node coordinates prevent nearest-node collisions and choosing a
    strongly connected component ensures a road path exists in both directions.
    """
    components = nx.strongly_connected_components(graph)
    component = max(components, key=len)
    candidates = sorted(component)

    if len(candidates) < count:
        raise ValueError(
            f"Kothrud graph needs {count} connected nodes; found {len(candidates)}"
        )

    selected = [candidates[0]]
    while len(selected) < count:
        def nearest_squared_distance(node):
            node_data = graph.nodes[node]
            return min(
                (node_data["x"] - graph.nodes[current]["x"]) ** 2
                + (node_data["y"] - graph.nodes[current]["y"]) ** 2
                for current in selected
            )

        selected.append(max(candidates, key=nearest_squared_distance))

    locations = []
    for location_id, node in enumerate(selected):
        data = graph.nodes[node]
        locations.append({
            "id": location_id,
            "name": "Kothrud depot" if location_id == 0 else f"Kothrud customer {location_id}",
            "latitude": float(data["y"]),
            "longitude": float(data["x"]),
        })
    return locations


def create_kothrud_problem():
    """Create the built-in real-road / simulated-traffic demo problem."""
    return create_kothrud_problem_with_incident()


def create_kothrud_problem_with_incident(incident_leg=None, incident_factor=None):
    """Create Kothrud data, optionally slowing one edge of a route leg.

    ``incident_leg`` contains two RouteX location IDs, for example ``(0, 2)``.
    The selected OSM edge is on that exact directed road path, so the incident
    genuinely affects the route that triggered re-optimization.
    """
    graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))
    locations = _connected_locations(graph)

    incident_edges = None
    incident_metadata = None
    if incident_leg is not None:
        if incident_factor is None:
            incident_factor = 0.25
        if not 0 < float(incident_factor) <= 1:
            raise ValueError("incident_factor must satisfy 0 < factor <= 1")

        source_id, target_id = incident_leg
        if not 0 <= source_id < len(locations) or not 0 <= target_id < len(locations):
            raise ValueError("incident leg contains an unknown location id")

        source = next(
            node for node, data in graph.nodes(data=True)
            if data["y"] == locations[source_id]["latitude"]
            and data["x"] == locations[source_id]["longitude"]
        )
        target = next(
            node for node, data in graph.nodes(data=True)
            if data["y"] == locations[target_id]["latitude"]
            and data["x"] == locations[target_id]["longitude"]
        )
        path = nx.shortest_path(graph, source, target, weight="length")
        if len(path) < 2:
            raise ValueError("incident leg has no road edge")

        edge_data = graph.get_edge_data(path[0], path[1])
        edge_key = min(edge_data, key=lambda key: edge_data[key].get("length", 0))
        affected_edge = (path[0], path[1], edge_key)
        incident_edges = {affected_edge: float(incident_factor)}
        incident_metadata = {
            "type": "simulated road-speed incident",
            "leg": [source_id, target_id],
            "edge": list(affected_edge),
            "speed_factor": float(incident_factor),
        }

    matrix_data = build_route_matrix(
        graph,
        locations,
        traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
        incident_edges=incident_edges,
    )

    problem = ProblemInstance(
        distance_matrix=matrix_data["distance_matrix"],
        travel_time_matrix=matrix_data["travel_time_matrix"],
        vehicles=[
            {"id": 1, "capacity": 7},
            {"id": 2, "capacity": 7},
        ],
        customers=[
            {"id": 1, "demand": 2},
            {"id": 2, "demand": 3},
            {"id": 3, "demand": 2},
            {"id": 4, "demand": 3},
        ],
        metadata={
            **matrix_data["metadata"],
            "source": "Kothrud OSM extract with simulated traffic",
            "traffic_factors": KOTHRUD_TRAFFIC_FACTORS,
            "locations": locations,
            "incident": incident_metadata,
        },
    )
    return problem
