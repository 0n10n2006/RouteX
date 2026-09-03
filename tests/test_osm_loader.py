import networkx as nx
import pytest

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
    get_congestion_factor,
    get_low_congestion_factor,
    get_medium_congestion_factor,
    get_high_congestion_factor,
    get_edge_capacity,
    get_dynamic_travel_time,
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


def test_get_congestion_factor():
    low = get_congestion_factor("low")
    medium = get_congestion_factor("medium")
    high = get_congestion_factor("high")

    print("Low congestion factor:", low)
    print("Medium congestion factor:", medium)
    print("High congestion factor:", high)

    assert isinstance(low, float)
    assert isinstance(medium, float)
    assert isinstance(high, float)

    assert low == 1.0
    assert medium == 1.5
    assert high == 2.0

    assert low < medium < high


def test_get_low_congestion_factor():
    factor = get_low_congestion_factor()

    print("Low congestion factor:", factor)

    assert isinstance(factor, float)
    assert factor == 1.0


def test_get_medium_congestion_factor():
    factor = get_medium_congestion_factor()

    print("Medium congestion factor:", factor)

    assert isinstance(factor, float)
    assert factor == 1.5


def test_get_high_congestion_factor():
    factor = get_high_congestion_factor()

    print("High congestion factor:", factor)

    assert isinstance(factor, float)
    assert factor == 2.0


def test_invalid_congestion_level():
    with pytest.raises(ValueError):
        get_congestion_factor("invalid")

def test_get_edge_capacity():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    capacity = get_edge_capacity(
        graph,
        source,
        target,
    )

    print("Source:", source)
    print("Target:", target)
    print("Edge capacity:", capacity, "vehicles/hour")

    assert isinstance(capacity, float)
    assert capacity > 0


def test_road_capacity_values():
    graph = nx.MultiDiGraph()

    graph.add_node(1, x=73.8, y=18.5)
    graph.add_node(2, x=73.81, y=18.51)

    graph.add_edge(
        1,
        2,
        highway="primary",
        length=500,
    )

    capacity = get_edge_capacity(
        graph,
        1,
        2,
    )

    print(
        "Primary road capacity:",
        capacity,
        "vehicles/hour",
    )

    assert capacity == 1500.0


def test_capacity_changes_by_road_type():
    graph = nx.MultiDiGraph()

    graph.add_node(1, x=73.8, y=18.5)
    graph.add_node(2, x=73.81, y=18.51)
    graph.add_node(3, x=73.82, y=18.52)

    graph.add_edge(
        1,
        2,
        highway="primary",
        length=500,
    )

    graph.add_edge(
        2,
        3,
        highway="residential",
        length=500,
    )

    primary_capacity = get_edge_capacity(
        graph,
        1,
        2,
    )

    residential_capacity = get_edge_capacity(
        graph,
        2,
        3,
    )

    print(
        "Primary capacity:",
        primary_capacity,
    )

    print(
        "Residential capacity:",
        residential_capacity,
    )

    assert primary_capacity > residential_capacity


def test_unknown_road_capacity():
    graph = nx.MultiDiGraph()

    graph.add_node(1, x=73.8, y=18.5)
    graph.add_node(2, x=73.81, y=18.51)

    graph.add_edge(
        1,
        2,
        highway="unknown",
        length=500,
    )

    capacity = get_edge_capacity(
        graph,
        1,
        2,
    )

    print(
        "Unknown road capacity:",
        capacity,
        "vehicles/hour",
    )

    assert capacity == 500.0

def test_get_dynamic_travel_time():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    dynamic_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="normal",
        congestion_level="low",
    )

    print(
        "Dynamic travel time:",
        dynamic_time,
        "seconds",
    )

    assert isinstance(dynamic_time, float)
    assert dynamic_time > 0


def test_dynamic_travel_time_uses_traffic_factor():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    base_time = get_edge_travel_time(
        graph,
        source,
        target,
    )

    off_peak_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="off_peak",
        congestion_level="low",
    )

    peak_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="peak",
        congestion_level="low",
    )

    print("Base travel time:", base_time)
    print("Off-peak travel time:", off_peak_time)
    print("Peak travel time:", peak_time)

    assert off_peak_time == base_time
    assert peak_time > off_peak_time


def test_dynamic_travel_time_uses_congestion():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    low_congestion_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="normal",
        congestion_level="low",
    )

    medium_congestion_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="normal",
        congestion_level="medium",
    )

    high_congestion_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="normal",
        congestion_level="high",
    )

    print(
        "Low congestion time:",
        low_congestion_time,
    )

    print(
        "Medium congestion time:",
        medium_congestion_time,
    )

    print(
        "High congestion time:",
        high_congestion_time,
    )

    assert low_congestion_time < medium_congestion_time
    assert medium_congestion_time < high_congestion_time


def test_dynamic_travel_time_calculation():
    graph = load_road_network(
        "data/raw/kothrud_test_area.osm"
    )

    graph = prepare_graph(graph)

    source, target = list(graph.edges())[0][0:2]

    base_time = get_edge_travel_time(
        graph,
        source,
        target,
    )

    traffic_factor = get_traffic_factor(
        "peak"
    )

    congestion_factor = get_congestion_factor(
        "high"
    )

    dynamic_time = get_dynamic_travel_time(
        graph,
        source,
        target,
        traffic_state="peak",
        congestion_level="high",
    )

    expected_time = (
        base_time
        * traffic_factor
        * congestion_factor
    )

    print("Base travel time:", base_time)
    print("Traffic factor:", traffic_factor)
    print("Congestion factor:", congestion_factor)
    print("Dynamic travel time:", dynamic_time)
    print("Expected travel time:", expected_time)

    assert dynamic_time == expected_time