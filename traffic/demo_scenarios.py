from pathlib import Path

from traffic.graph_builder import close_road
from traffic.simulation import load_simulation_network


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LARGER_OSM_FILE = PROJECT_ROOT / "data" / "raw" / "larger_area.osm"


DEMO_LOCATION_NODES = [
    245646149,
    9230260511,
    4704949764,
]


DEMO_ROUTES = [
    [0, 1, 2],
    [0, 1, 2],
]


DEMO_INCIDENT_EDGE = (
    4704949756,
    4704949764,
    0,
)


def get_demo_graph():
    return load_simulation_network(LARGER_OSM_FILE)


def get_demo_locations(graph):
    locations = []

    for location_id, node in enumerate(DEMO_LOCATION_NODES):
        if node not in graph.nodes:
            raise ValueError(
                f"Demo location node does not exist: {node}"
            )

        node_data = graph.nodes[node]

        locations.append(
            {
                "id": location_id,
                "name": (
                    "Demo depot"
                    if location_id == 0
                    else f"Demo location {location_id}"
                ),
                "latitude": float(node_data["y"]),
                "longitude": float(node_data["x"]),
            }
        )

    return locations


def get_demo_setup():
    graph = get_demo_graph()
    locations = get_demo_locations(graph)
    routes = [route.copy() for route in DEMO_ROUTES]

    return graph, locations, routes


def get_demo_incident_edge():
    return DEMO_INCIDENT_EDGE


def create_normal_demo():
    graph, locations, routes = get_demo_setup()

    return {
        "name": "normal",
        "description": "Normal traffic on the real OSM network",
        "graph": graph,
        "locations": locations,
        "routes": routes,
        "traffic_factors": None,
        "incident_edges": None,
    }


def create_heavy_traffic_demo():
    graph, locations, routes = get_demo_setup()

    heavy_traffic = {
        "primary": 0.45,
        "secondary": 0.50,
        "tertiary": 0.55,
        "residential": 0.45,
        "service": 0.45,
        "default": 0.50,
    }

    return {
        "name": "heavy_traffic",
        "description": "Heavy simulated traffic on the real OSM network",
        "graph": graph,
        "locations": locations,
        "routes": routes,
        "traffic_factors": heavy_traffic,
        "incident_edges": None,
    }


def create_incident_demo():
    graph, locations, routes = get_demo_setup()

    incident_edge = get_demo_incident_edge()

    if not graph.has_edge(*incident_edge):
        raise ValueError(
            f"Demo incident edge does not exist: {incident_edge}"
        )

    return {
        "name": "incident",
        "description": "Simulated slowdown on a route edge",
        "graph": graph,
        "locations": locations,
        "routes": routes,
        "traffic_factors": None,
        "incident_edges": {
            incident_edge: 0.25
        },
        "incident_edge": incident_edge,
    }


def create_closure_demo():
    graph, locations, routes = get_demo_setup()

    closed_edge = get_demo_incident_edge()

    if not graph.has_edge(*closed_edge):
        raise ValueError(
            f"Demo closure edge does not exist: {closed_edge}"
        )

    closed_graph = close_road(
        graph,
        [closed_edge],
    )

    return {
        "name": "closure",
        "description": "Simulated road closure with rerouting",
        "graph": closed_graph,
        "original_graph": graph,
        "locations": locations,
        "routes": routes,
        "traffic_factors": None,
        "incident_edges": None,
        "closed_edge": closed_edge,
    }


def create_all_demo_scenarios():
    return [
        create_normal_demo(),
        create_heavy_traffic_demo(),
        create_incident_demo(),
        create_closure_demo(),
    ]