from pathlib import Path

import osmnx as ox


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