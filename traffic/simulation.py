from dataclasses import dataclass, field

import networkx as nx

from traffic.graph_builder import (
    _nearest_node,
    _prepare_travel_times,
)
from traffic.osm_loader import load_road_network, prepare_graph


@dataclass
class VehicleState:
    """
    Current state of one simulated vehicle.
    """

    vehicle_id: int
    route: list
    current_location_index: int = 0
    path_nodes: list = field(default_factory=list)
    path_position: int = 0
    remaining_edge_time: float = 0.0
    current_edge_total_time: float = 0.0
    current_edge_distance: float = 0.0
    elapsed_time: float = 0.0
    travelled_distance: float = 0.0
    status: str = "ready"
    current_edge: tuple | None = None


@dataclass
class SimulationState:
    """
    Current state of the complete traffic simulation.
    """

    vehicles: list
    elapsed_time: float = 0.0
    edge_load: dict = field(default_factory=dict)
    completed: bool = False


def load_simulation_network(osm_file):
    """
    Load and prepare an OSM road network for simulation.
    """

    graph = load_road_network(osm_file)
    return prepare_graph(graph)


def _location_nodes(graph, locations):
    """
    Convert simulation locations into their nearest OSM graph nodes.
    """

    if not isinstance(locations, list) or not locations:
        raise ValueError("locations must be a non-empty list")

    result = {}

    for location in locations:
        if not isinstance(location, dict):
            raise ValueError("Each location must be a dictionary")

        if "id" not in location:
            raise ValueError("Each location must contain an id")

        node = _nearest_node(graph, location)
        result[location["id"]] = node

    return result


def _build_vehicle_path(
    graph,
    location_nodes,
    route,
    travel_graph,
):
    """
    Convert a location route into actual OSM road nodes.
    """

    if not isinstance(route, list) or len(route) < 2:
        raise ValueError(
            "Each vehicle route must contain at least two locations"
        )

    for location_id in route:
        if location_id not in location_nodes:
            raise ValueError(
                f"Route references unknown location {location_id}"
            )

    path_nodes = []

    for source_id, target_id in zip(route, route[1:]):
        try:
            leg_nodes = nx.shortest_path(
                travel_graph,
                location_nodes[source_id],
                location_nodes[target_id],
                weight="travel_time",
            )
        except nx.NetworkXNoPath:
            raise ValueError(
                f"No route exists between location "
                f"{source_id} and location {target_id}"
            )

        path_nodes.extend(
            leg_nodes if not path_nodes else leg_nodes[1:]
        )

    return path_nodes


def create_vehicle_states(
    graph,
    locations,
    routes,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Create simulation states for optimizer vehicle routes.
    """

    if not isinstance(routes, list):
        raise ValueError("routes must be a list")

    location_nodes = _location_nodes(
        graph,
        locations,
    )

    travel_graph = _prepare_travel_times(
        graph,
        traffic_factors,
        incident_edges,
    )

    vehicles = []

    for vehicle_index, route in enumerate(routes, start=1):
        path_nodes = _build_vehicle_path(
            graph,
            location_nodes,
            route,
            travel_graph,
        )

        vehicles.append(
            VehicleState(
                vehicle_id=vehicle_index,
                route=route,
                path_nodes=path_nodes,
                status="ready",
            )
        )

    return vehicles


def _edge_data(graph, u, v):
    """
    Return the first edge data for a directed road segment.
    """

    if not graph.has_edge(u, v):
        raise ValueError(
            f"Road edge does not exist: {(u, v)}"
        )

    data = graph.get_edge_data(u, v)

    key = next(iter(data))
    return key, data[key]


def _update_vehicle_edge(
    vehicle,
    graph,
    travel_graph,
):
    """
    Prepare the vehicle to travel across its current edge.
    """

    if vehicle.path_position >= len(vehicle.path_nodes) - 1:
        vehicle.current_edge = None
        vehicle.remaining_edge_time = 0.0
        vehicle.current_edge_total_time = 0.0
        vehicle.current_edge_distance = 0.0
        vehicle.status = "completed"
        return

    u = vehicle.path_nodes[vehicle.path_position]
    v = vehicle.path_nodes[vehicle.path_position + 1]

    key, original_data = _edge_data(graph, u, v)

    if not travel_graph.has_edge(u, v):
        raise ValueError(
            f"Travel edge is unavailable: {(u, v, key)}"
        )

    travel_data = travel_graph.get_edge_data(u, v)[key]

    vehicle.current_edge = (u, v, key)

    vehicle.remaining_edge_time = float(
        travel_data["travel_time"]
    )

    vehicle.current_edge_total_time = float(
        travel_data["travel_time"]
    )

    vehicle.current_edge_distance = float(
        original_data.get("length", 0.0)
    )


def _advance_vehicle(
    vehicle,
    graph,
    travel_graph,
    time_step,
):
    """
    Advance one vehicle by a fixed simulation time step.
    """

    if vehicle.status == "completed":
        return

    if vehicle.status == "ready":
        _update_vehicle_edge(
            vehicle,
            graph,
            travel_graph,
        )

        if vehicle.status == "completed":
            return

        vehicle.status = "moving"

    remaining_step = float(time_step)

    while remaining_step > 0 and vehicle.status != "completed":

        if vehicle.remaining_edge_time <= 0:
            _update_vehicle_edge(
                vehicle,
                graph,
                travel_graph,
            )

            if vehicle.status == "completed":
                break

        movement_time = min(
            remaining_step,
            vehicle.remaining_edge_time,
        )

        vehicle.remaining_edge_time -= movement_time
        vehicle.elapsed_time += movement_time
        remaining_step -= movement_time

        if vehicle.current_edge_total_time > 0:
            distance_fraction = (
                movement_time
                / vehicle.current_edge_total_time
            )
        else:
            distance_fraction = 1.0

        vehicle.travelled_distance += (
            vehicle.current_edge_distance
            * distance_fraction
        )

        if vehicle.remaining_edge_time <= 0:
            vehicle.path_position += 1
            vehicle.current_edge = None

            if vehicle.path_position >= len(vehicle.path_nodes) - 1:
                vehicle.status = "completed"
                vehicle.current_edge = None
                vehicle.remaining_edge_time = 0.0
                vehicle.current_edge_total_time = 0.0
                vehicle.current_edge_distance = 0.0
            else:
                _update_vehicle_edge(
                    vehicle,
                    graph,
                    travel_graph,
                )


def calculate_network_loading(vehicles):
    """
    Count the number of active vehicles on each road edge.
    """

    edge_load = {}

    for vehicle in vehicles:
        if (
            vehicle.status == "moving"
            and vehicle.current_edge is not None
        ):
            edge = vehicle.current_edge
            edge_load[edge] = edge_load.get(edge, 0) + 1

    return edge_load


def create_simulation(
    graph,
    locations,
    routes,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Create a new traffic simulation.
    """

    vehicles = create_vehicle_states(
        graph,
        locations,
        routes,
        traffic_factors=traffic_factors,
        incident_edges=incident_edges,
    )

    return SimulationState(
        vehicles=vehicles,
        elapsed_time=0.0,
        edge_load={},
        completed=False,
    )


def step_simulation(
    simulation,
    graph,
    time_step=1.0,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Advance the simulation by one time step.
    """

    if not isinstance(simulation, SimulationState):
        raise ValueError(
            "simulation must be a SimulationState"
        )

    if time_step <= 0:
        raise ValueError(
            "time_step must be greater than zero"
        )

    travel_graph = _prepare_travel_times(
        graph,
        traffic_factors,
        incident_edges,
    )

    for vehicle in simulation.vehicles:
        _advance_vehicle(
            vehicle,
            graph,
            travel_graph,
            time_step,
        )

    simulation.elapsed_time += float(time_step)

    simulation.edge_load = calculate_network_loading(
        simulation.vehicles
    )

    simulation.completed = all(
        vehicle.status == "completed"
        for vehicle in simulation.vehicles
    )

    return simulation


def run_simulation(
    graph,
    locations,
    routes,
    time_step=1.0,
    max_time=3600.0,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Run a complete traffic simulation.
    """

    simulation = create_simulation(
        graph,
        locations,
        routes,
        traffic_factors=traffic_factors,
        incident_edges=incident_edges,
    )

    while (
        not simulation.completed
        and simulation.elapsed_time < max_time
    ):
        step_simulation(
            simulation,
            graph,
            time_step=time_step,
            traffic_factors=traffic_factors,
            incident_edges=incident_edges,
        )

    return simulation