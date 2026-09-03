import networkx as nx
import pytest

from traffic.graph_builder import apply_incident, build_route_matrix


def make_graph():
    graph = nx.MultiDiGraph()

    graph.add_edge(
        0,
        1,
        key=0,
        length=1000,
        highway="primary",
    )
    graph.add_edge(
        1,
        0,
        key=0,
        length=1000,
        highway="primary",
    )

    graph.add_edge(
        1,
        2,
        key=0,
        length=1000,
        highway="secondary",
    )
    graph.add_edge(
        2,
        1,
        key=0,
        length=1000,
        highway="secondary",
    )

    graph.nodes[0]["x"] = 73.8000
    graph.nodes[0]["y"] = 18.5000
    graph.nodes[1]["x"] = 73.8010
    graph.nodes[1]["y"] = 18.5010
    graph.nodes[2]["x"] = 73.8020
    graph.nodes[2]["y"] = 18.5020

    graph.graph["crs"] = "EPSG:4326"

    return graph


def test_build_route_matrix():
    graph = make_graph()

    locations = [
        {
            "id": 0,
            "name": "Depot",
            "latitude": 18.5000,
            "longitude": 73.8000,
        },
        {
            "id": 1,
            "name": "Customer 1",
            "latitude": 18.5010,
            "longitude": 73.8010,
        },
        {
            "id": 2,
            "name": "Customer 2",
            "latitude": 18.5020,
            "longitude": 73.8020,
        },
    ]

    result = build_route_matrix(graph, locations)

    assert len(result["distance_matrix"]) == 3
    assert len(result["travel_time_matrix"]) == 3

    assert result["distance_matrix"][0][1] == pytest.approx(1000)
    assert result["distance_matrix"][0][2] == pytest.approx(2000)

    assert result["travel_time_matrix"][0][1] > 0
    assert result["travel_time_matrix"][0][2] > 0


def test_apply_incident_changes_travel_time():
    graph = make_graph()

    normal = build_route_matrix(
        graph,
        [
            {"id": 0, "latitude": 18.5000, "longitude": 73.8000},
            {"id": 1, "latitude": 18.5010, "longitude": 73.8010},
        ],
    )

    incident_graph = apply_incident(
        graph,
        {
            "edges": [(0, 1, 0)],
            "factor": 0.5,
        },
    )

    incident = build_route_matrix(
        incident_graph,
        [
            {"id": 0, "latitude": 18.5000, "longitude": 73.8000},
            {"id": 1, "latitude": 18.5010, "longitude": 73.8010},
        ],
    )

    assert incident["distance_matrix"][0][1] == pytest.approx(
        normal["distance_matrix"][0][1]
    )

    assert incident["travel_time_matrix"][0][1] == pytest.approx(
        normal["travel_time_matrix"][0][1] * 2
    )


def test_apply_incident_rejects_invalid_factor():
    graph = make_graph()

    with pytest.raises(ValueError):
        apply_incident(
            graph,
            {
                "edges": [(0, 1, 0)],
                "factor": 0,
            },
        )


def test_apply_incident_rejects_missing_edge():
    graph = make_graph()

    with pytest.raises(ValueError):
        apply_incident(
            graph,
            {
                "edges": [(99, 100, 0)],
                "factor": 0.5,
            },
        )


def test_apply_incident_does_not_modify_original_graph():
    graph = make_graph()

    incident_graph = apply_incident(
        graph,
        {
            "edges": [(0, 1, 0)],
            "factor": 0.5,
        },
    )

    assert "incident_factor" not in graph[0][1][0]
    assert incident_graph[0][1][0]["incident_factor"] == pytest.approx(0.5)