from pathlib import Path

import osmnx as ox


ROAD_SPEEDS = {
    "motorway": 100,
    "trunk": 90,
    "primary": 60,
    "secondary": 50,
    "tertiary": 40,
    "residential": 30,
    "unclassified": 30,
    "service": 20,
}


TRAFFIC_FACTORS = {
    "off_peak": 1.0,
    "normal": 1.25,
    "peak": 1.75,
}


def load_road_network(osm_file):
    """Load an OSM road network into a NetworkX graph."""
    osm_path = Path(osm_file)

    graph = ox.graph_from_xml(
        osm_path,
        bidirectional=False,
        simplify=True,
    )

    return graph


def prepare_graph(graph):
    """Ensure required basic road attributes exist on every edge."""
    for _, _, _, data in graph.edges(
        keys=True,
        data=True,
    ):
        if "length" not in data:
            data["length"] = 0

        if "highway" not in data:
            data["highway"] = "unknown"

    return graph


def find_shortest_path(graph, source, target):
    """Find the shortest path using edge length."""
    return ox.shortest_path(
        graph,
        source,
        target,
        weight="length",
    )


def get_edge_distance(graph, source, target):
    """Return the distance of a road edge in meters."""
    edge_data = graph.get_edge_data(source, target)

    if edge_data is None:
        raise ValueError(
            f"No edge exists between {source} and {target}"
        )

    first_edge = next(iter(edge_data.values()))

    return float(first_edge["length"])


def get_edge_speed(graph, source, target):
    """Return the assumed speed of a road edge in km/h."""
    edge_data = graph.get_edge_data(source, target)

    if edge_data is None:
        raise ValueError(
            f"No edge exists between {source} and {target}"
        )

    first_edge = next(iter(edge_data.values()))

    highway = first_edge.get("highway", "unknown")

    if isinstance(highway, list):
        highway = highway[0]

    return float(ROAD_SPEEDS.get(highway, 30))


def get_edge_travel_time(graph, source, target):
    """Return the estimated travel time of a road edge in seconds."""
    distance = get_edge_distance(
        graph,
        source,
        target,
    )

    speed = get_edge_speed(
        graph,
        source,
        target,
    )

    if speed <= 0:
        raise ValueError("Speed must be greater than zero.")

    return (distance / speed) * 3.6


def get_traffic_factor(traffic_state):
    """Return the multiplier for a traffic state."""
    if traffic_state not in TRAFFIC_FACTORS:
        raise ValueError(
            f"Unknown traffic state: {traffic_state}"
        )

    return float(TRAFFIC_FACTORS[traffic_state])


def get_off_peak_factor():
    """Return the traffic factor for off-peak conditions."""
    return get_traffic_factor("off_peak")


def get_normal_factor():
    """Return the traffic factor for normal conditions."""
    return get_traffic_factor("normal")


def get_peak_factor():
    """Return the traffic factor for peak conditions."""
    return get_traffic_factor("peak")