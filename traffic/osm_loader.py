from pathlib import Path

import osmnx as ox


def load_road_network(osm_file):
    osm_path = Path(osm_file)

    graph = ox.graph_from_xml(
        osm_path,
        bidirectional=False,
        simplify=True
    )

    return graph


def prepare_graph(graph):
    for source, target, key, data in graph.edges(
        keys=True,
        data=True
    ):
        if "length" not in data:
            data["length"] = 0

        if "highway" not in data:
            data["highway"] = "unknown"

    return graph