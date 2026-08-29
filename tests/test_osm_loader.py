import networkx as nx

from traffic.osm_loader import (
    load_road_network,
    prepare_graph,
    find_shortest_path,
)


def test_load_road_network():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    print("Number of nodes:", len(graph.nodes))
    print("Number of edges:", len(graph.edges))

    node_id = list(graph.nodes)[0]
    node_data = graph.nodes[node_id]

    print("Sample node ID:", node_id)
    print("Sample node data:", node_data)

    assert graph is not None
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0

    assert "x" in node_data
    assert "y" in node_data

    source, target, edge_data = list(
        graph.edges(data=True)
    )[0]

    print("Sample edge:", source, "->", target)
    print("Edge data:", edge_data)

    assert "length" in edge_data
    assert edge_data["length"] > 0

    print("Highway type:", edge_data.get("highway"))

    assert "highway" in edge_data


def test_prepare_graph_missing_attributes():
    graph = nx.MultiDiGraph()

    graph.add_node(1, x=73.8, y=18.5)
    graph.add_node(2, x=73.81, y=18.51)

    graph.add_edge(1, 2)

    graph = prepare_graph(graph)

    edge_data = graph.edges[1, 2, 0]

    print("Prepared edge data:", edge_data)

    assert "length" in edge_data
    assert "highway" in edge_data

    assert edge_data["length"] == 0
    assert edge_data["highway"] == "unknown"


def test_find_shortest_path():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    path = find_shortest_path(
        graph,
        source,
        target
    )

    print("Source:", source)
    print("Target:", target)
    print("Shortest path:", path)

    assert path is not None
    assert len(path) >= 2
    assert path[0] == source
    assert path[-1] == target


def test_shortest_path_exists_in_graph():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    path = find_shortest_path(
        graph,
        source,
        target
    )

    print("Path to verify:", path)

    assert path is not None
    assert len(path) >= 2

    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]

        assert graph.has_edge(
            current_node,
            next_node
        )


def test_graph_supports_routing():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    # Select a connected pair of nodes from an existing edge.
    source, target = list(graph.edges())[0][0:2]

    path = find_shortest_path(
        graph,
        source,
        target
    )

    print("Routing source:", source)
    print("Routing target:", target)
    print("Routing path:", path)

    assert path is not None
    assert len(path) >= 2
    assert path[0] == source
    assert path[-1] == target

def test_traffic_graph_pipeline():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    path = find_shortest_path(
        graph,
        source,
        target
    )

    print("Integration graph nodes:", len(graph.nodes))
    print("Integration graph edges:", len(graph.edges))
    print("Integration route:", path)

    assert graph is not None
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0

    assert path is not None
    assert len(path) >= 2