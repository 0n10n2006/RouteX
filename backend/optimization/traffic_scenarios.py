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

# Stable, known OSM edges from the committed Kothrud extract. These names make
# repeated before/after experiments reproducible and easy to discuss in demos.
DEFAULT_KOTHRUD_INCIDENT_SCENARIO = "kothrud_connector_slowdown"
KOTHRUD_INCIDENT_SCENARIOS = {
    "kothrud_connector_slowdown": {
        "edge": (1563310394, 4704828557, 0),
        "description": "Simulated slowdown on the Kothrud connector road",
    },
}


def resolve_kothrud_incident(incident_edge=None, incident_scenario=None):
    """Resolve an explicit OSM edge or a stable named incident scenario."""
    if incident_edge is not None and incident_scenario is not None:
        raise ValueError("Provide either incident_edge or incident_scenario, not both")

    if incident_edge is not None:
        if (
            not isinstance(incident_edge, (list, tuple))
            or len(incident_edge) != 3
            or any(not isinstance(value, int) or isinstance(value, bool) for value in incident_edge)
        ):
            raise ValueError("incident_edge must be [u, v, key] using integer OSM IDs")
        return {
            "scenario": "custom_osm_edge",
            "edge": tuple(incident_edge),
            "description": "Simulated slowdown on a user-selected OSM edge",
        }

    name = (incident_scenario or DEFAULT_KOTHRUD_INCIDENT_SCENARIO).lower().strip()
    definition = KOTHRUD_INCIDENT_SCENARIOS.get(name)
    if definition is None:
        available = ", ".join(sorted(KOTHRUD_INCIDENT_SCENARIOS))
        raise ValueError(f"Unknown incident_scenario '{name}'. Available: {available}")

    return {
        "scenario": name,
        "edge": definition["edge"],
        "description": definition["description"],
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
    graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))
    return _create_kothrud_problem(graph)


def _create_kothrud_problem(graph, incident_edges=None, incident_metadata=None):
    locations = _connected_locations(graph)

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


def create_kothrud_problem_with_incident(
    incident_edge,
    incident_factor=0.25,
    incident_scenario="custom_osm_edge",
    incident_description=None,
):
    """Create Kothrud data with a slowdown on one exact directed OSM edge."""
    if not 0 < float(incident_factor) <= 1:
        raise ValueError("incident_factor must satisfy 0 < factor <= 1")

    graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))
    affected_edge = tuple(incident_edge)
    if not graph.has_edge(*affected_edge):
        raise ValueError(f"Incident edge does not exist in Kothrud graph: {affected_edge}")

    incident_metadata = {
        "type": "simulated road-speed incident",
        "scenario": incident_scenario,
        "description": incident_description,
        "edge": list(affected_edge),
        "speed_factor": float(incident_factor),
    }
    return _create_kothrud_problem(
        graph,
        incident_edges={affected_edge: float(incident_factor)},
        incident_metadata=incident_metadata,
    )
