# RouteX API Contract

**Audience:** Parag (frontend and visualisation)

Base URL during local development: `http://127.0.0.1:8000`

The frontend must call this FastAPI API only. It must never import or run an
optimizer directly. JSON requests use the header `Content-Type: application/json`.

## Current data status

- The `kothrud` scenario uses real road geometry from the committed Kothrud OSM
  extract. Its traffic factors and incidents are **simulated**, not live data.
- `kothrud` returns road distance in metres and simulated travel time in seconds.
  Matrix-only scenarios retain their original test-distance objective and return
  `travel_time: null`.
- For `kothrud`, `fitness` is simulated traffic-adjusted travel time. For all
  other current scenarios, it remains distance.
- A JSON `null` means the value is unavailable or the optimizer did not find a
  JSON-safe finite value.

## Shared types

### Route

```json
[0, 4, 3, 2, 1, 0]
```

An ordered list of node IDs. `0` is the depot; every route should start and end
at it. A run's `routes` value is a list of vehicle routes.

### Customer

```json
{"id": 1, "demand": 2}
```

### Vehicle

```json
{"id": 1, "capacity": 10}
```

### Optimization run

```json
{
  "id": 101,
  "algorithm": "QPSO",
  "fitness": 43.0,
  "created_at": "2026-08-31 10:44:45",
  "distance": 43.0,
  "runtime": 0.0025,
  "scenario": "default",
  "routes": [[0, 4, 3, 2, 1, 0]],
  "convergence": [57.0, 48.0, 43.0],
  "iterations": 20,
  "constraint_violations": 0,
  "vehicles_used": 1,
  "seed": 1001,
  "travel_time": null,
  "congestion_penalty": null,
  "fuel_cost": null
}
```

Field meanings:

| Field | Meaning |
| --- | --- |
| `id` | Persistent SQLite run ID. |
| `algorithm` | Display name: `QPSO`, `Hybrid QPSO + 2-opt`, or `Greedy (classical baseline)`. |
| `fitness` | Score to minimise: simulated travel time for `kothrud`, otherwise distance. |
| `distance` | Total road distance in metres for `kothrud`; test-matrix units otherwise. |
| `runtime` | Optimizer execution time in seconds. |
| `scenario` | Resolved scenario name. An unknown requested name resolves safely to `default`. |
| `routes` | One route list for each used vehicle. |
| `convergence` | Best fitness after each QPSO iteration. Greedy returns `[]`. |
| `iterations` | `20` for QPSO/hybrid; `0` for greedy. |
| `constraint_violations` | Count of failed route checks. `0` means feasible. |
| `vehicles_used` | Number of returned route lists. |
| `seed` | Optional reproducibility seed; `null` when not supplied. |
| `travel_time` | Simulated traffic-adjusted seconds for `kothrud`; `null` for matrix-only scenarios. |
| `traffic_metadata` | OSM/traffic provenance, location coordinates, and any incident details. |

## Endpoints

### `GET /`

Health check and supported built-in values.

Response:

```json
{
  "message": "RouteX Backend is running!",
  "algorithms": ["greedy", "qpso", "hybrid"],
  "scenarios": ["default", "low", "medium", "high", "big", "kothrud"]
}
```

### `POST /optimize`

Runs one algorithm, saves it to SQLite, and returns the new run.

Request body (all fields optional):

```json
{
  "algorithm": "qpso",
  "scenario": "big",
  "seed": 1001
}
```

| Field | Allowed value / behaviour |
| --- | --- |
| `algorithm` | `greedy`, `qpso`, or `hybrid`. Any other value currently runs QPSO. Frontend must send one of the three listed values. |
| `scenario` | A built-in name or a custom scenario name from `GET /scenarios`. Unknown names use `default`. |
| `seed` | Integer or `null`. The same scenario + algorithm + seed is reproducible. |

Response: an optimization-run object plus `run_id` and `feasible`.

```json
{
  "run_id": 101,
  "algorithm": "QPSO",
  "scenario": "big",
  "fitness": 137.0,
  "distance": 137.0,
  "runtime": 0.0037,
  "routes": [[0, 1, 2, 0], [0, 3, 4, 5, 6, 0]],
  "vehicles_used": 2,
  "iterations": 20,
  "constraint_violations": 0,
  "feasible": true,
  "seed": 1001,
  "convergence": [168.0, 151.0, 137.0]
}
```

### `GET /results?limit=<integer>`

Returns saved runs newest first. Omit `limit` for all rows.

Response:

```json
{"results": [/* optimization-run objects */]}
```

### `POST /optimize/kothrud-incident`

Runs Kothrud optimization, slows an OSM edge on the initial route, then
re-optimizes. Both runs are saved and returned. OSM geometry is real; the
speed reduction is simulated.

```json
{"algorithm": "hybrid", "seed": 42, "incident_factor": 0.25}
```

`incident_factor` must be greater than `0` and at most `1`; lower values mean a
slower affected road. The response contains `before`, `after_incident`, and
the selected OSM `incident` edge.

### `GET /results/comparison`

Returns the best observed result per scenario and display algorithm. Rows sort by
scenario, then lowest fitness.

Response:

```json
{
  "comparison": [
    {
      "scenario": "big",
      "algorithm": "QPSO",
      "best_fitness": 137.0,
      "best_runtime": 0.0019,
      "runs": 3
    }
  ]
}
```

### `GET /results/{run_id}`

Returns one full optimization-run object, including `routes` and `convergence`.

Error response if the ID does not exist:

```json
{"detail": "No run with id 99999"}
```

Status: `404`.

### `GET /results/{run_id}/convergence`

Returns only chart data for one saved run.

```json
{
  "run_id": 101,
  "algorithm": "QPSO",
  "scenario": "big",
  "iterations": 20,
  "convergence": [168.0, 151.0, 137.0]
}
```

For greedy, `convergence` is `[]` and `iterations` is `0`; show no line chart.
Missing IDs return the same `404` shape as `GET /results/{run_id}`.

### `GET /scenarios`

Returns all built-in and custom scenarios in stable numeric-ID order. Use this to
populate the scenario selector; do not hardcode a dropdown.

```json
{
  "scenarios": [
    {
      "id": 5,
      "name": "big",
      "description": "Harder benchmark — 6 customers, 3 vehicles, capacity binds",
      "source": "builtin",
      "num_customers": 6,
      "num_vehicles": 3,
      "total_demand": 21,
      "distance_matrix": [[0, 12], [12, 0]],
      "vehicles": [{"id": 1, "capacity": 10}],
      "customers": [{"id": 1, "demand": 4}],
      "created_at": "2026-08-31 10:00:00"
    }
  ]
}
```

### `POST /scenarios`

Creates a custom scenario, or updates the existing scenario with the same name.
The supplied name is lowercased and trimmed.

```json
{
  "name": "kothrud_test",
  "description": "Small custom test",
  "distance_matrix": [[0, 5, 8], [5, 0, 4], [8, 4, 0]],
  "vehicles": [{"id": 1, "capacity": 10}],
  "customers": [{"id": 1, "demand": 3}, {"id": 2, "demand": 4}]
}
```

The matrix must contain the depot plus every customer ID. For a highest customer
ID of `2`, it must have at least three rows. Non-empty `vehicles` and `customers`
are required.

Success response:

```json
{"scenario_id": 6, "scenario": {/* full scenario object */}}
```

Validation errors return status `400` with `{ "detail": "..." }`.

### `GET /scenarios/{identifier}`

Gets one full scenario. `identifier` may be its numeric `id` or its `name`.

Examples: `/scenarios/5`, `/scenarios/big`

Missing scenarios return status `404`:

```json
{"detail": "No scenario 'missing_name'"}
```

### `POST /benchmark`

Runs every selected algorithm × scenario × seed, saves every individual run, and
returns both raw runs and aggregate statistics. This endpoint can take noticeable
time; show a loading state and disable the trigger while it runs.

Request body is optional. Default: `3` seeds, all five built-in scenarios, and
all three algorithms.

```json
{
  "seeds": 3,
  "scenarios": ["big", "high"],
  "algorithms": ["greedy", "qpso", "hybrid"]
}
```

`seeds` is clamped to `1`–`10`. Omit `scenarios` or `algorithms` to use their
defaults.

```json
{
  "total_runs": 18,
  "seeds_per_combination": 3,
  "scenarios": ["big", "high"],
  "algorithms": ["greedy", "qpso", "hybrid"],
  "total_runtime": 0.231,
  "summary": [
    {
      "scenario": "big",
      "algorithm": "QPSO",
      "runs": 3,
      "feasible_runs": 3,
      "best_fitness": 137.0,
      "mean_fitness": 140.0,
      "worst_fitness": 146.0,
      "mean_runtime": 0.00231,
      "improvement_vs_baseline_percent": 16.7
    }
  ],
  "runs": [
    {
      "run_id": 101,
      "scenario": "big",
      "algorithm": "QPSO",
      "fitness": 137.0,
      "runtime": 0.00231,
      "feasible": true,
      "seed": 1000
    }
  ]
}
```

`improvement_vs_baseline_percent` is calculated against greedy's mean fitness
for the same scenario. It is `null` for the greedy baseline and when no baseline
exists. Higher positive values are better.

## Frontend handling rules

1. Always check `response.ok`. FastAPI errors use `{ "detail": "message" }`.
2. Render `null` as `—`, never as `0`.
3. Use `routes` from a result detail or optimize response to draw route lines.
4. Use `convergence` only when it has at least two numeric values.
5. Treat all current map distances as demo/test data until the traffic graph is
   integrated.
