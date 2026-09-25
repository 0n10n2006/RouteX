import math

import networkx as nx
import osmnx as ox

from .osm_loader import ROAD_SPEEDS


DEFAULT_SPEED = 30.0


def _validate_locations(locations):
    if not isinstance(locations, list) or not locations:
        raise ValueError("locations must be a non-empty list")

    ids = []

    for location in locations:
        if not isinstance(location, dict):
            raise ValueError("Each location must be a dictionary")

        location_id = location.get("id")

        if (
            not isinstance(location_id, int)
            or isinstance(location_id, bool)
            or location_id < 0
        ):
            raise ValueError("Location ids must be non-negative integers")

        if location_id in ids:
            raise ValueError(f"Duplicate location id: {location_id}")

        if "latitude" not in location or "longitude" not in location:
            raise ValueError(
                f"Location {location_id} must contain latitude and longitude"
            )

        ids.append(location_id)

    if ids[0] != 0:
        raise ValueError("Location id 0 must be the depot")

    if set(ids) != set(range(len(ids))):
        raise ValueError(
            "Location ids must be contiguous starting at 0"
        )


def _edge_highway(data):
    highway = data.get("highway", "unknown")

    if isinstance(highway, list):
        highway = highway[0] if highway else "unknown"

    return highway


def _edge_speed(data):
    """
    Return edge speed in km/h.

    Uses maxspeed when it is a usable numeric value.
    Otherwise falls back deterministically to ROAD_SPEEDS.
    """
    maxspeed = data.get("maxspeed")

    if isinstance(maxspeed, list):
        maxspeed = maxspeed[0] if maxspeed else None

    if isinstance(maxspeed, (int, float)):
        if maxspeed > 0:
            return float(maxspeed)

    if isinstance(maxspeed, str):
        try:
            value = float(maxspeed.split()[0])
            if value > 0:
                return value
        except (ValueError, IndexError):
            pass

    return float(ROAD_SPEEDS.get(_edge_highway(data), DEFAULT_SPEED))


def _traffic_factor_for_edge(data, traffic_factors):
    if traffic_factors is None:
        return 1.0

    highway = _edge_highway(data)

    factor = traffic_factors.get(
        highway,
        traffic_factors.get("default", 1.0),
    )

    factor = float(factor)

    if not 0 < factor <= 1:
        raise ValueError(
            f"Traffic factor must satisfy 0 < factor <= 1: {factor}"
        )

    return factor


def _incident_factor_for_edge(u, v, key, data, incident_edges):
    if "incident_factor" in data:
        return float(data["incident_factor"])

    if incident_edges is None:
        return 1.0

    factor = incident_edges.get((u, v, key), 1.0)

    factor = float(factor)

    if not 0 < factor <= 1:
        raise ValueError(
            f"Incident factor must satisfy 0 < factor <= 1: {factor}"
        )

    return factor


def _prepare_travel_times(graph, traffic_factors, incident_edges):
    graph = graph.copy()

    for u, v, key, data in graph.edges(
        keys=True,
        data=True,
    ):
        length = float(data.get("length", 0))

        if length < 0:
            raise ValueError(
                f"Edge {u}, {v}, {key} has negative length"
            )

        speed_kmh = _edge_speed(data)

        traffic_factor = _traffic_factor_for_edge(
            data,
            traffic_factors,
        )

        incident_factor = _incident_factor_for_edge(
            u,
            v,
            key,
            data,
            incident_edges,
        )

        effective_speed_kmh = (
            speed_kmh
            * traffic_factor
            * incident_factor
        )

        if effective_speed_kmh <= 0:
            raise ValueError(
                f"Edge {u}, {v}, {key} has invalid effective speed"
            )

        speed_mps = effective_speed_kmh / 3.6

        data["travel_time"] = length / speed_mps

    return graph


def _nearest_node(graph, location):
    latitude = float(location["latitude"])
    longitude = float(location["longitude"])

    return ox.distance.nearest_nodes(
        graph,
        X=longitude,
        Y=latitude,
    )


def build_route_matrix(
    graph,
    locations,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Build road-network distance and traffic-adjusted travel-time matrices.
    """

    _validate_locations(locations)

    if not isinstance(graph, (nx.Graph, nx.DiGraph)):
        raise ValueError("graph must be a NetworkX graph")

    node_lookup = {}

    for location in locations:
        location_id = location["id"]

        node_lookup[str(location_id)] = _nearest_node(
            graph,
            location,
        )

    travel_graph = _prepare_travel_times(
        graph,
        traffic_factors,
        incident_edges,
    )

    count = len(locations)

    distance_matrix = [
        [0.0 for _ in range(count)]
        for _ in range(count)
    ]

    travel_time_matrix = [
        [0.0 for _ in range(count)]
        for _ in range(count)
    ]

    for source_id in range(count):
        source_node = node_lookup[str(source_id)]

        for target_id in range(count):
            if source_id == target_id:
                continue

            target_node = node_lookup[str(target_id)]

            try:
                distance = nx.shortest_path_length(
                    graph,
                    source_node,
                    target_node,
                    weight="length",
                )

                travel_time = nx.shortest_path_length(
                    travel_graph,
                    source_node,
                    target_node,
                    weight="travel_time",
                )

            except nx.NetworkXNoPath:
                raise ValueError(
                    f"No route exists between location "
                    f"{source_id} and location {target_id}"
                )

            distance = float(distance)
            travel_time = float(travel_time)

            if not math.isfinite(distance):
                raise ValueError(
                    f"Non-finite distance for locations "
                    f"{source_id} and {target_id}"
                )

            if not math.isfinite(travel_time):
                raise ValueError(
                    f"Non-finite travel time for locations "
                    f"{source_id} and {target_id}"
                )

            distance_matrix[source_id][target_id] = distance
            travel_time_matrix[source_id][target_id] = travel_time

    return {
        "distance_matrix": distance_matrix,
        "travel_time_matrix": travel_time_matrix,
        "node_lookup": node_lookup,
        "metadata": {
            "distance_unit": "metres",
            "travel_time_unit": "seconds",
            "location_count": count,
            "traffic_model": (
                "effective_speed = "
                "base_speed * traffic_factor * incident_factor"
            ),
            "graph_crs": "EPSG:4326",
        },
    }


def build_route_geometry(
    graph,
    locations,
    routes,
    traffic_factors=None,
    incident_edges=None,
):
    """
    Return road-following GeoJSON features for optimizer vehicle routes.

    Coordinates use GeoJSON order: [longitude, latitude].
    Each feature is one vehicle route stitched from the shortest
    traffic-adjusted OSM paths for its route legs.
    """

    _validate_locations(locations)

    if not isinstance(routes, list):
        raise ValueError("routes must be a list")

    location_nodes = {
        location["id"]: _nearest_node(graph, location)
        for location in locations
    }

    travel_graph = _prepare_travel_times(
        graph,
        traffic_factors,
        incident_edges,
    )

    features = []

    for vehicle_index, route in enumerate(routes, start=1):
        if not isinstance(route, list) or len(route) < 2:
            raise ValueError(
                f"Route {vehicle_index} must contain at least two locations"
            )

        if any(
            location_id not in location_nodes
            for location_id in route
        ):
            raise ValueError(
                f"Route {vehicle_index} references an unknown location"
            )

        path_nodes = []

        for source_id, target_id in zip(route, route[1:]):
            if source_id == target_id:
                continue
            src_node = location_nodes.get(source_id)
            tgt_node = location_nodes.get(target_id)
            if src_node is None or tgt_node is None:
                continue
            try:
                leg_nodes = nx.shortest_path(
                    travel_graph,
                    src_node,
                    tgt_node,
                    weight="travel_time",
                )
                path_nodes.extend(
                    leg_nodes if not path_nodes else leg_nodes[1:]
                )
            except (nx.NetworkXNoPath, nx.NodeNotFound, KeyError):
                # If no road path exists between these two points in the graph,
                # bridge with the endpoint coordinates directly so the route stays intact
                pass

        if path_nodes:
            coordinates = [
                [
                    float(graph.nodes[node]["x"]),
                    float(graph.nodes[node]["y"]),
                ]
                for node in path_nodes
            ]
        else:
            # Fallback to straight lines connecting route stops
            loc_by_id = {loc["id"]: loc for loc in locations}
            coordinates = [
                [float(loc_by_id[lid]["longitude"]), float(loc_by_id[lid]["latitude"])]
                for lid in route
                if lid in loc_by_id
            ]

        if len(coordinates) >= 2:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "vehicle_index": vehicle_index,
                        "route": route,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coordinates,
                    },
                }
            )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def _osrm_route(waypoints, timeout=5):
    """Call the OSRM demo router for road-following geometry.

    *waypoints* is a list of [longitude, latitude] pairs.
    Returns a list of [lng, lat] coordinates tracing the road, or None on
    failure (network error, rate limit, bad response).
    """
    import requests as _requests

    if len(waypoints) < 2:
        return None

    coords_str = ";".join(f"{lng},{lat}" for lng, lat in waypoints)
    url = (
        f"https://router.project-osrm.org/route/v1/driving/{coords_str}"
        f"?overview=full&geometries=geojson"
    )

    try:
        resp = _requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("code") != "Ok":
            return None
        route_geom = data["routes"][0]["geometry"]["coordinates"]
        if len(route_geom) >= 2:
            return route_geom
        return None
    except Exception:
        return None


def build_straight_line_geometry(locations, routes):
    """Return straight-line GeoJSON features connecting route stops.

    Last-resort fallback when neither the local OSM graph nor OSRM are
    available.
    """
    _validate_locations(locations)
    loc_by_id = {loc["id"]: loc for loc in locations}
    features = []

    for vehicle_index, route in enumerate(routes, start=1):
        if not isinstance(route, list) or len(route) < 2:
            continue
        if all(loc_id == 0 for loc_id in route):
            continue

        coordinates = []
        for loc_id in route:
            if loc_id in loc_by_id:
                loc = loc_by_id[loc_id]
                coordinates.append([float(loc["longitude"]), float(loc["latitude"])])

        if len(coordinates) >= 2:
            features.append({
                "type": "Feature",
                "properties": {
                    "vehicle_index": vehicle_index,
                    "route": route,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def build_osrm_geometry(locations, routes):
    """Return road-following GeoJSON via the OSRM public routing API.

    Each vehicle route is sent to OSRM as a sequence of waypoints.  OSRM
    returns the actual road path (the same roads a car would drive on),
    giving a realistic route overlay on the map.

    Falls back to straight-line geometry if OSRM is unreachable.
    """
    _validate_locations(locations)
    loc_by_id = {loc["id"]: loc for loc in locations}
    features = []

    for vehicle_index, route in enumerate(routes, start=1):
        if not isinstance(route, list) or len(route) < 2:
            continue
        if all(loc_id == 0 for loc_id in route):
            continue

        # Build waypoint list for this vehicle
        waypoints = []
        for loc_id in route:
            if loc_id in loc_by_id:
                loc = loc_by_id[loc_id]
                waypoints.append([float(loc["longitude"]), float(loc["latitude"])])

        if len(waypoints) < 2:
            continue

        # Try OSRM for road-following geometry
        road_coords = _osrm_route(waypoints)

        # Use road coords if available, otherwise fall back to straight lines
        coordinates = road_coords if road_coords else waypoints

        if len(coordinates) >= 2:
            features.append({
                "type": "Feature",
                "properties": {
                    "vehicle_index": vehicle_index,
                    "route": route,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def apply_incident(graph, incident):
    """
    Return a copy of graph with an incident speed factor applied.
    """

    if not isinstance(incident, dict):
        raise ValueError("incident must be a dictionary")

    edges = incident.get("edges")
    factor = incident.get("factor")

    if not isinstance(edges, list) or not edges:
        raise ValueError(
            "incident.edges must be a non-empty list"
        )

    try:
        factor = float(factor)

    except (TypeError, ValueError):
        raise ValueError(
            "incident factor must be numeric"
        )

    if not 0 < factor <= 1:
        raise ValueError(
            "incident factor must satisfy 0 < factor <= 1"
        )

    result = graph.copy()

    for edge in edges:
        if not isinstance(edge, (tuple, list)) or len(edge) != 3:
            raise ValueError(
                "Each incident edge must be (u, v, key)"
            )

        u, v, key = edge

        if not result.has_edge(u, v, key):
            raise ValueError(
                f"Incident edge does not exist: {(u, v, key)}"
            )

        result[u][v][key]["incident_factor"] = factor

    return result


def close_road(graph, edges):
    """
    Return a copy of the graph with the specified road edges removed.

    A closed road cannot be used by routing or shortest-path calculations.
    """

    if not isinstance(edges, list) or not edges:
        raise ValueError(
            "edges must be a non-empty list"
        )

    result = graph.copy()

    for edge in edges:
        if not isinstance(edge, (tuple, list)) or len(edge) != 3:
            raise ValueError(
                "Each closed edge must be (u, v, key)"
            )

        u, v, key = edge

        if not result.has_edge(u, v, key):
            raise ValueError(
                f"Closed edge does not exist: {(u, v, key)}"
            )

        result.remove_edge(u, v, key)

    return result