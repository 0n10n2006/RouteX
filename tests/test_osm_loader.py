import networkx as nx

from traffic.osm_loader import (
    load_road_network,
    prepare_graph,
    find_shortest_path,
    get_edge_distance,
    get_edge_speed,
    get_edge_travel_time,
    get_traffic_factor,
    get_off_peak_factor,
    get_normal_factor,
    get_peak_factor,
)


def test_load_road_network():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    print("Number of nodes:", len(graph.nodes))
    print("Number of edges:", len(graph.edges))

    assert graph is not None
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0

    node_id = list(graph.nodes)[0]
    node_data = graph.nodes[node_id]

    print("Sample node ID:", node_id)
    print("Sample node data:", node_data)

    assert "x" in node_data
    assert "y" in node_data

    source, target, edge_data = list(
        graph.edges(data=True)
    )[0]

    print("Sample edge:", source, "->", target)
    print("Edge data:", edge_data)

    assert "length" in edge_data
    assert edge_data["length"] > 0
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
        target,
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
        target,
    )

    print("Path to verify:", path)

    assert path is not None
    assert len(path) >= 2

    for i in range(len(path) - 1):
        current_node = path[i]
        next_node = path[i + 1]

        assert graph.has_edge(
            current_node,
            next_node,
        )


def test_graph_supports_routing():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    path = find_shortest_path(
        graph,
        source,
        target,
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
        target,
    )

    print(
        "Integration graph nodes:",
        len(graph.nodes),
    )

    print(
        "Integration graph edges:",
        len(graph.edges),
    )

    print("Integration route:", path)

    assert graph is not None
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    assert path is not None
    assert len(path) >= 2


def test_get_edge_distance():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    distance = get_edge_distance(
        graph,
        source,
        target,
    )

    print("Source:", source)
    print("Target:", target)
    print("Edge distance:", distance, "meters")

    assert isinstance(distance, float)
    assert distance > 0


def test_get_edge_speed():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    speed = get_edge_speed(
        graph,
        source,
        target,
    )

    print("Source:", source)
    print("Target:", target)
    print("Edge speed:", speed, "km/h")

    assert isinstance(speed, float)
    assert speed > 0


def test_get_edge_travel_time():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

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

    travel_time = get_edge_travel_time(
        graph,
        source,
        target,
    )

    expected_time = (distance / speed) * 3.6

    print("Distance:", distance, "meters")
    print("Speed:", speed, "km/h")
    print("Travel time:", travel_time, "seconds")

    assert isinstance(travel_time, float)
    assert travel_time > 0
    assert travel_time == expected_time


def test_get_traffic_factor():
    off_peak = get_traffic_factor("off_peak")
    normal = get_traffic_factor("normal")
    peak = get_traffic_factor("peak")

    print("Off-peak factor:", off_peak)
    print("Normal factor:", normal)
    print("Peak factor:", peak)

    assert isinstance(off_peak, float)
    assert isinstance(normal, float)
    assert isinstance(peak, float)

    assert off_peak == 1.0
    assert normal == 1.25
    assert peak == 1.75

    assert off_peak < normal < peak


def test_get_off_peak_factor():
    factor = get_off_peak_factor()

    print("Off-peak traffic factor:", factor)

    assert isinstance(factor, float)
    assert factor == 1.0


def test_get_normal_factor():
    factor = get_normal_factor()

    print("Normal traffic factor:", factor)

    assert isinstance(factor, float)
    assert factor == 1.25
def test_get_peak_factor():
    factor = get_peak_factor()

    print("Peak traffic factor:", factor)

    assert isinstance(factor, float)
    assert factor == 1.75