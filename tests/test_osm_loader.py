from traffic.osm_loader import load_road_network, prepare_graph


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