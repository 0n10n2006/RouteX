# RouteX Traffic Graph → Optimizer Contract

**Owner:** Zobiya (traffic graph)<br>
**Consumer:** Ali (FastAPI, SQLite, integration)<br>
**Status:** Integration contract only — traffic-aware routing is not implemented yet.

## Purpose

RouteX needs a small adapter boundary between the OSMnx/NetworkX road graph and
the existing optimizer. The optimizer does not need the full graph: it needs a
square distance matrix indexed by the depot/customer IDs it already understands.

The adapter must use road-network shortest paths, not straight-line distance.

## Required functions

Place these in `traffic/graph_builder.py`. They must be importable without
starting a server or downloading map data.

```python
def build_route_matrix(graph, locations, traffic_factors=None, incident_edges=None):
    """Return road-network distance/time data for the requested locations."""


def apply_incident(graph, incident):
    """Return a copy of graph with the incident applied; do not mutate graph."""
```

## Input: `locations`

```python
locations = [
    {"id": 0, "name": "Depot", "latitude": 18.5204, "longitude": 73.8567},
    {"id": 1, "name": "Customer 1", "latitude": 18.5314, "longitude": 73.8446},
    {"id": 2, "name": "Customer 2", "latitude": 18.5074, "longitude": 73.8077}
]
```

Rules:

1. `id` values must be non-negative integers and unique.
2. `id: 0` is always the depot.
3. IDs must be contiguous (`0, 1, ..., n`) so matrix row/column `i` means
   location ID `i`. If source IDs are not contiguous, the graph layer must
   renumber them and return the mapping in `node_lookup`.
4. Latitude and longitude are WGS84 decimal degrees.

## Output: `build_route_matrix`

Return exactly this dictionary shape:

```python
{
    "distance_matrix": [
        [0.0, 1240.5, 2075.2],
        [1202.1, 0.0, 980.4],
        [2101.8, 1001.7, 0.0]
    ],
    "travel_time_matrix": [
        [0.0, 186.1, 311.3],
        [180.3, 0.0, 147.1],
        [315.3, 150.3, 0.0]
    ],
    "node_lookup": {
        "0": 123456,
        "1": 234567,
        "2": 345678
    },
    "metadata": {
        "distance_unit": "metres",
        "travel_time_unit": "seconds",
        "location_count": 3,
        "traffic_model": "effective_speed = base_speed * traffic_factor * incident_factor",
        "graph_crs": "EPSG:4326"
    }
}
```

### Matrix rules

- Both matrices are `n × n`, where `n == len(locations)`.
- Every value must be a finite number (`int` or `float`), never `None`, `NaN`,
  or `Infinity`.
- The diagonal is `0.0`.
- `distance_matrix[a][b]` is shortest **road distance in metres** from `a` to
  `b`. Do not assume it is symmetric: one-way streets make it directional.
- `travel_time_matrix[a][b]` is shortest traffic-adjusted road travel time in
  **seconds** from `a` to `b`.
- If no route exists, raise `ValueError` with the two location IDs. Do not
  silently substitute an aerial distance or huge fake penalty.

## Traffic calculation

For every graph edge, calculate:

```text
effective_speed = base_speed × traffic_factor × incident_factor
travel_time = edge_length_metres / effective_speed_metres_per_second
```

Requirements:

- Use an edge's mapped speed when it exists; otherwise use one documented,
  deterministic road-class fallback speed.
- `traffic_factor` and `incident_factor` are multipliers in `(0, 1]`.
- Store the traffic-adjusted value on the **copied graph** as edge attribute
  `travel_time` (seconds), then calculate shortest paths using `weight="travel_time"`.
- Calculate `distance_matrix` with `weight="length"`, separately from travel time.

## Input: traffic and incidents

`traffic_factors` is optional. When omitted, every edge uses `1.0`.

```python
traffic_factors = {
    "primary": 0.65,
    "secondary": 0.80,
    "default": 1.0,
}
```

`incident_edges` is optional. When omitted, every edge uses `1.0`.

```python
incident_edges = {
    (123456, 234567, 0): 0.25
}
```

The key is the NetworkX edge `(u, v, key)` and the value is its incident speed
multiplier. An incident factor of `0.25` means that edge operates at 25% of its
otherwise effective speed. Do not use `0`: the edge remains passable and the
route can be compared before and after an incident.

## `apply_incident` contract

Input:

```python
incident = {
    "edges": [(123456, 234567, 0)],
    "factor": 0.25,
    "description": "Lane closure on NH 60"
}
```

Behaviour:

1. Make and return a graph copy.
2. Validate `0 < factor <= 1` and that every requested edge exists.
3. Apply the factor only to the listed directed edges.
4. Do not edit the source graph and do not recalculate an optimizer route here.

## What Ali will integrate

Once the functions above exist, the backend adapter will:

1. Turn selected depot/customer coordinates into `locations`.
2. Pass `distance_matrix` to the existing `ProblemInstance` unchanged.
3. Save real `travel_time`, `congestion_penalty`, and `fuel_cost` only after
   the agreed fitness formula is implemented and verified.
4. Add incident re-optimization as a separate API endpoint. It will not be
   added before the graph contract is available and tested.

## Acceptance test

Before requesting integration, provide a runnable test using three locations
that proves all of the following:

1. Output matrices are 3×3, finite, and have zero diagonals.
2. A traffic factor below `1.0` increases at least one travel-time value while
   leaving distance values unchanged.
3. Applying an incident returns a new graph, leaves the original graph unchanged,
   and increases the affected route's travel time or causes a valid reroute.
4. A shortest road path is used for every matrix entry.
