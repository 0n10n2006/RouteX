import pytest

from traffic.demo_scenarios import (
    DEMO_INCIDENT_EDGE,
    DEMO_LOCATION_NODES,
    DEMO_ROUTES,
    create_all_demo_scenarios,
    create_closure_demo,
    create_incident_demo,
    create_normal_demo,
)


def test_demo_configuration_is_fixed():
    assert DEMO_LOCATION_NODES == [
        245646149,
        9230260511,
        4704949764,
    ]

    assert DEMO_ROUTES == [
        [0, 1, 2],
        [0, 1, 2],
    ]

    assert DEMO_INCIDENT_EDGE == (
        4704949756,
        4704949764,
        0,
    )


def test_all_demo_scenarios_are_available():
    scenarios = create_all_demo_scenarios()

    assert len(scenarios) == 4

    assert [scenario["name"] for scenario in scenarios] == [
        "normal",
        "heavy_traffic",
        "incident",
        "closure",
    ]


def test_normal_demo_configuration():
    scenario = create_normal_demo()

    assert scenario["name"] == "normal"
    assert scenario["traffic_factors"] is None
    assert scenario["incident_edges"] is None
    assert scenario["routes"] == DEMO_ROUTES


def test_incident_demo_uses_fixed_edge():
    scenario = create_incident_demo()

    assert scenario["name"] == "incident"

    assert scenario["incident_edge"] == (
        DEMO_INCIDENT_EDGE
    )

    assert scenario["incident_edges"] == {
        DEMO_INCIDENT_EDGE: 0.25
    }

    assert scenario["graph"].has_edge(
        *DEMO_INCIDENT_EDGE
    )


def test_closure_demo_removes_fixed_edge():
    scenario = create_closure_demo()

    assert scenario["name"] == "closure"

    assert scenario["closed_edge"] == (
        DEMO_INCIDENT_EDGE
    )

    assert scenario["original_graph"].has_edge(
        *DEMO_INCIDENT_EDGE
    )

    assert not scenario["graph"].has_edge(
        *DEMO_INCIDENT_EDGE
    )


def test_demo_locations_match_fixed_nodes():
    scenario = create_normal_demo()

    locations = scenario["locations"]

    assert len(locations) == 3

    for location, expected_node in zip(
        locations,
        DEMO_LOCATION_NODES,
    ):
        graph = scenario["graph"]

        assert location["latitude"] == pytest.approx(
            graph.nodes[expected_node]["y"]
        )

        assert location["longitude"] == pytest.approx(
            graph.nodes[expected_node]["x"]
        )