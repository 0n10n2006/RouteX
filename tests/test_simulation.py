import networkx as nx
import pytest

from traffic.graph_builder import close_road
from traffic.simulation import (
    calculate_network_loading,
    create_simulation,
    create_vehicle_states,
    run_simulation,
    step_simulation,
)


def make_graph():
    graph = nx.MultiDiGraph()

    # Main route
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

    # Alternative route around 0 -> 1
    graph.add_edge(
        0,
        3,
        key=0,
        length=700,
        highway="primary",
    )

    graph.add_edge(
        3,
        1,
        key=0,
        length=700,
        highway="primary",
    )

    graph.nodes[0]["x"] = 73.8000
    graph.nodes[0]["y"] = 18.5000

    graph.nodes[1]["x"] = 73.8010
    graph.nodes[1]["y"] = 18.5010

    graph.nodes[2]["x"] = 73.8020
    graph.nodes[2]["y"] = 18.5020

    graph.nodes[3]["x"] = 73.7990
    graph.nodes[3]["y"] = 18.4990

    graph.graph["crs"] = "EPSG:4326"

    return graph


def make_locations():
    return [
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


def test_create_vehicle_states_builds_road_path():
    graph = make_graph()
    locations = make_locations()

    vehicles = create_vehicle_states(
        graph,
        locations,
        routes=[[0, 1, 2]],
    )

    assert len(vehicles) == 1

    vehicle = vehicles[0]

    assert vehicle.vehicle_id == 1
    assert vehicle.route == [0, 1, 2]
    assert vehicle.path_nodes == [0, 1, 2]
    assert vehicle.status == "ready"


def test_vehicle_moves_during_simulation_step():
    graph = make_graph()
    locations = make_locations()

    simulation = create_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
    )

    step_simulation(
        simulation,
        graph,
        time_step=30,
    )

    vehicle = simulation.vehicles[0]

    assert simulation.elapsed_time == pytest.approx(30)
    assert vehicle.status == "moving"
    assert vehicle.current_edge == (0, 1, 0)
    assert vehicle.travelled_distance == pytest.approx(500)
    assert simulation.edge_load[(0, 1, 0)] == 1


def test_network_loading_counts_multiple_vehicles():
    graph = make_graph()
    locations = make_locations()

    simulation = create_simulation(
        graph,
        locations,
        routes=[
            [0, 1, 2],
            [0, 1, 2],
        ],
    )

    step_simulation(
        simulation,
        graph,
        time_step=1,
    )

    assert simulation.edge_load[(0, 1, 0)] == 2


def test_calculate_network_loading_ignores_completed_vehicles():
    graph = make_graph()
    locations = make_locations()

    simulation = create_simulation(
        graph,
        locations,
        routes=[[0, 1]],
    )

    vehicle = simulation.vehicles[0]

    vehicle.status = "completed"
    vehicle.current_edge = None

    loading = calculate_network_loading(
        simulation.vehicles
    )

    assert loading == {}


def test_run_simulation_completes_vehicle_route():
    graph = make_graph()
    locations = make_locations()

    simulation = run_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
        time_step=1,
        max_time=300,
    )

    vehicle = simulation.vehicles[0]

    assert simulation.completed is True
    assert vehicle.status == "completed"
    assert vehicle.travelled_distance == pytest.approx(2000)
    assert vehicle.elapsed_time == pytest.approx(132)
    assert simulation.edge_load == {}


def test_simulation_rejects_invalid_time_step():
    graph = make_graph()
    locations = make_locations()

    simulation = create_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
    )

    with pytest.raises(ValueError):
        step_simulation(
            simulation,
            graph,
            time_step=0,
        )


def test_incident_slowdown_increases_travel_time():
    graph = make_graph()
    locations = make_locations()

    normal = run_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
        time_step=1,
        max_time=1000,
    )

    incident = run_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
        time_step=1,
        max_time=1000,
        incident_edges={
            (0, 1, 0): 0.25
        },
    )

    assert normal.completed is True
    assert incident.completed is True

    # The incident makes the affected road slower,
    # so the resulting trip should take longer.
    assert (
        incident.vehicles[0].elapsed_time
        > normal.vehicles[0].elapsed_time
    )

    # The incident may cause rerouting, so the new
    # route can be longer than the normal route.
    assert (
        incident.vehicles[0].travelled_distance
        >= normal.vehicles[0].travelled_distance
    )


def test_road_closure_reroutes_vehicle():
    graph = make_graph()
    locations = make_locations()

    normal = create_simulation(
        graph,
        locations,
        routes=[[0, 1, 2]],
    )

    closed_graph = close_road(
        graph,
        [(0, 1, 0)],
    )

    closed = create_simulation(
        closed_graph,
        locations,
        routes=[[0, 1, 2]],
    )

    # Normal route uses the original road.
    assert normal.vehicles[0].path_nodes == [
        0,
        1,
        2,
    ]

    # Closed route must use the alternative road.
    assert closed.vehicles[0].path_nodes == [
        0,
        3,
        1,
        2,
    ]

    closed_path_edges = [
        (
            closed.vehicles[0].path_nodes[index],
            closed.vehicles[0].path_nodes[index + 1],
            0,
        )
        for index in range(
            len(closed.vehicles[0].path_nodes) - 1
        )
    ]

    # The closed road must not appear in the new route.
    assert (0, 1, 0) not in closed_path_edges

    result = run_simulation(
        closed_graph,
        locations,
        routes=[[0, 1, 2]],
        time_step=1,
        max_time=1000,
    )

    assert result.completed is True
    assert result.vehicles[0].status == "completed"

    # Alternative route is longer:
    # 700 + 700 + 1000 = 2400 m
    assert result.vehicles[0].travelled_distance == pytest.approx(
        2400
    )