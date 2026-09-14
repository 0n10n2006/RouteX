import random

from backend.optimization.benchmark import run_qpso
from backend.optimization.traffic_scenarios import (
    KOTHRUD_TRAFFIC_FACTORS,
)
from traffic.graph_builder import build_route_geometry
from traffic.simulation import (
    load_simulation_network,
    run_simulation,
)


def test_qpso_result_can_run_through_traffic_simulation():
    """
    End-to-end check:

    Real OSM graph
        -> traffic-aware optimizer problem
        -> QPSO
        -> optimized location routes
        -> road-network simulation
    """

    random.seed(1)

    # Use the same real OSM network already used by
    # the Kothrud optimization scenarios.
    from backend.optimization.traffic_scenarios import (
        KOTHRUD_OSM_FILE,
        _connected_locations,
    )
    from traffic.osm_loader import (
        load_road_network,
        prepare_graph,
    )
    from traffic.graph_builder import (
        build_route_matrix,
    )
    from backend.optimization.problem import ProblemInstance

    graph = prepare_graph(
        load_road_network(KOTHRUD_OSM_FILE)
    )

    locations = _connected_locations(
        graph,
        count=5,
    )

    matrix_data = build_route_matrix(
        graph,
        locations,
        traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
    )

    problem = ProblemInstance(
        distance_matrix=matrix_data["distance_matrix"],
        travel_time_matrix=matrix_data["travel_time_matrix"],
        vehicles=[
            {"id": 1, "capacity": 7},
            {"id": 2, "capacity": 7},
        ],
        customers=[
            {"id": 1, "demand": 2},
            {"id": 2, "demand": 3},
            {"id": 3, "demand": 2},
            {"id": 4, "demand": 3},
        ],
        metadata={
            **matrix_data["metadata"],
            "source": "Kothrud OSM extract with simulated traffic",
            "traffic_factors": KOTHRUD_TRAFFIC_FACTORS,
            "locations": locations,
        },
    )

    # Confirm that this really is a traffic-aware problem.
    assert problem.travel_time_matrix is not None

    result = run_qpso(
        problem,
        num_particles=5,
        iterations=5,
        beta=0.5,
    )

    # QPSO must produce a feasible route.
    assert result["routes"]
    assert result["fitness"] != float("inf")

    # Convert the optimizer's location routes into actual
    # road-following geometry.
    geometry = build_route_geometry(
        graph,
        locations,
        result["routes"],
        traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
    )

    assert geometry["type"] == "FeatureCollection"
    assert geometry["features"]

    # Finally run the optimized routes through the
    # traffic simulation.
    simulation = run_simulation(
        graph,
        locations,
        result["routes"],
        time_step=5,
        max_time=7200,
        traffic_factors=KOTHRUD_TRAFFIC_FACTORS,
    )

    assert simulation.completed is True

    for vehicle in simulation.vehicles:
        assert vehicle.status == "completed"
        assert vehicle.travelled_distance > 0
        assert vehicle.elapsed_time > 0

    # All vehicles should have finished, so no active
    # network loading should remain.
    assert simulation.edge_load == {}