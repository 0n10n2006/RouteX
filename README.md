
# 🚚 RouteX
### Quantum-Inspired, Traffic-Aware Vehicle Routing Optimization

*Smarter last-mile delivery routes using Quantum Particle Swarm Optimization, real road networks, and live traffic — benchmarked, tested, and visualised end-to-end.*

</div>

---

## 1. The Problem We're Solving

Last-mile delivery and fleet routing is one of the most expensive parts of logistics — inefficient routes waste fuel, driver hours, and money, and get worse the moment real-world traffic and road incidents are added to the picture. Classical routing heuristics (nearest-neighbour, greedy assignment) are fast but shallow: they converge quickly to mediocre routes and don't adapt when the road network changes underneath them.

**RouteX** is a full-stack Vehicle Routing Problem (VRP) optimization platform that:

- Solves multi-vehicle, capacity-constrained routing using a **Quantum-behaved Particle Swarm Optimization (QPSO)** algorithm, benchmarked against Genetic Algorithms, classical PSO, and a Greedy baseline.
- Runs on **real road geometry** (OpenStreetMap road network for the Kothrud area, Pune) instead of toy distance matrices — routes actually follow streets.
- Reacts to **live traffic conditions** (TomTom Traffic API) and **simulated road incidents**, re-optimizing routes on the fly.
- Exposes everything through a documented **FastAPI backend + SQLite persistence layer**, and a **React + Leaflet + Recharts dashboard** for visual, judge-friendly demos.

---

## 2. What Makes RouteX Different (Unique Selling Points)

| # | Feature | Why it matters |
|---|---|---|
| 1 | **Hybrid QPSO + 2-opt metaheuristic** | Combines QPSO's global search with 2-opt local refinement — applied adaptively, only when QPSO finds a new global best — for faster, higher-quality convergence than either technique alone. |
| 2 | **Five algorithms benchmarked head-to-head in one platform** | Greedy, GA, PSO, QPSO, and Hybrid QPSO+2-opt all run against identical scenarios/seeds, so the improvement of quantum-inspired search over classical baselines is *measured*, not claimed. |
| 3 | **Real road-network routing, not a toy matrix** | Uses OSMnx + NetworkX to load an actual OSM extract of Kothrud, Pune, compute real shortest-path road distances, and render true polyline routes on a Leaflet map — not straight lines between dots. |
| 4 | **Live traffic + incident-aware re-optimization** | Integrates the TomTom Routing API for traffic-adjusted travel times, and can simulate a road slowdown/closure on an already-optimized route, then re-optimize to show the system adapting — a core "smart city" capability. |
| 5 | **Reproducible, seeded experimentation** | Every run accepts an optional seed; the same scenario + algorithm + seed always reproduces the same result — essential for fair benchmarking and for judges to verify claims live. |
| 6 | **Built-in statistical benchmarking endpoint** | `POST /benchmark` runs every algorithm × scenario × seed combination in one call and returns mean/best/worst fitness, runtime, and % improvement over the greedy baseline — no manual spreadsheet work needed. |
| 7 | **Full observability, not a black box** | Every run persists its convergence curve, constraint-violation count, vehicles used, distance, travel time, and fuel-cost placeholders to SQLite and exposes them via REST — the dashboard can chart *how* the algorithm converged, not just the final number. |
| 8 | **Clean separation of concerns** | Traffic/graph layer, optimization layer, and API/persistence layer are independent modules with a written contract (`docs/graph_specification.md`, `docs/API_CONTRACT.md`) — built by a 3-person team (traffic graph / optimization / backend+frontend) working in parallel without blocking each other. |

---

## 3. System Architecture

```
                         ┌─────────────────────────┐
                         │   React Dashboard        │
                         │  (Vite + Leaflet +       │
                         │   Recharts, axios)       │
                         └───────────┬──────────────┘
                                     │  REST/JSON
                                     ▼
                         ┌─────────────────────────┐
                         │   FastAPI Backend         │
                         │  /optimize  /benchmark     │
                         │  /scenarios /results       │
                         └───────┬─────────┬─────────┘
                                 │         │
                 ┌───────────────┘         └───────────────┐
                 ▼                                          ▼
   ┌─────────────────────────┐                ┌─────────────────────────┐
   │  Optimization Engine      │                │  Traffic / Graph Layer   │
   │  Greedy · GA · PSO ·       │◄──distance/────│  OSMnx + NetworkX        │
   │  QPSO · Hybrid QPSO+2opt   │  travel-time    │  OSM road extract        │
   │  fitness · constraints ·   │  matrix         │  Live traffic (TomTom)   │
   │  repair · local search      │                │  Incident simulation     │
   └───────────┬────────────────┘                └─────────────────────────┘
               │
               ▼
   ┌─────────────────────────┐
   │  SQLite persistence        │
   │  optimization_runs table   │
   │  scenarios table            │
   └─────────────────────────┘
```

The frontend **never calls the optimizer directly** — every interaction goes through the FastAPI contract, which keeps the system deployable, testable, and swappable (e.g. SQLite → Postgres later) without touching the UI.

---

## 4. Algorithms Implemented

- **Greedy VRP** — classical nearest-feasible-customer baseline; instant runtime, used as the improvement benchmark.
- **Genetic Algorithm (GA)** — population-based search with crossover/mutation over route permutations.
- **PSO** — standard particle swarm baseline for comparison against the quantum-behaved variant.
- **QPSO (Quantum-behaved PSO)** — particles governed by a quantum delta-potential-well model rather than classical velocity/position updates, with an **annealed contraction–expansion coefficient (β)** that anneals from a high value (broad exploration) to a low value (fine exploitation) over the run — this is what produces a genuine multi-step convergence curve instead of an instant jump to the optimum.
- **Hybrid QPSO + 2-opt** — QPSO handles global search; 2-opt local search is triggered adaptively whenever QPSO discovers a new global best, refining that specific solution without disturbing swarm diversity.

All five algorithms share the same **fitness function, constraint checker (capacity, depot start/end, full customer coverage), and solution-repair logic**, so comparisons are apples-to-apples.

---

## 5. Traffic & Road-Network Layer

- **`traffic/osm_loader.py`** — loads and caches an OSMnx road graph from a committed `.osm` extract of Kothrud, Pune, with road-class-based default speeds (motorway → service road) and time-of-day traffic-factor presets (off-peak / normal / peak).
- **`traffic/graph_builder.py`** — converts the road graph into the distance/travel-time matrix the optimizers consume, and can return **true road-following polyline geometry** (GeoJSON) for map rendering.
- **`traffic/live_traffic.py`** — an optional live-data client for the **TomTom Routing API**, fetching real traffic-adjusted travel times per origin–destination pair (concurrently, via a thread pool) when a `TOMTOM_API_KEY` is configured.
- **Incident simulation** — `POST /optimize/kothrud-incident` slows down (or effectively closes) a specific OSM road edge on an already-optimized route and re-optimizes with the same seed, returning a clean **before / after-incident** comparison plus the incident metadata — a compelling live demo of adaptive routing.

---

## 6. Backend API (FastAPI)

A fully documented contract lives in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md). Highlights:

| Endpoint | Purpose |
|---|---|
| `GET /` | Health check + supported algorithms/scenarios |
| `POST /optimize` | Run one algorithm on one scenario, persist and return the run |
| `POST /optimize/kothrud-incident` | Optimize → simulate an incident → re-optimize, same seed |
| `GET /results`, `GET /results/{id}` | Retrieve saved runs |
| `GET /results/{id}/geometry` | Road-following GeoJSON route for map rendering |
| `GET /results/{id}/convergence` | Iteration-by-iteration best-fitness curve |
| `GET /results/comparison` | Best result per scenario × algorithm |
| `GET /scenarios`, `POST /scenarios` | List built-in scenarios / register a custom one |
| `POST /benchmark` | Run every algorithm × scenario × seed combination and return aggregate statistics (mean, best, worst fitness/runtime, % improvement vs. greedy) |

Persistence is **SQLite** (`routex.db`) with two tables — `optimization_runs` (one row per algorithm run: fitness, distance, travel time, convergence curve, constraint violations, seed) and `scenarios` (named, reusable problem definitions) — designed so the schema can grow additively without breaking older rows.

---

## 7. Frontend Dashboard

A React (Vite) single-page dashboard (`frontend/routex-dashboard`) that gives judges a live, interactive view of the system:

- **Algorithm & scenario selector** with one-click optimization runs.
- **Leaflet map** rendering real road-following routes for OSM-backed scenarios (`RouteMap.jsx`).
- **Recharts** convergence line charts and algorithm-comparison bar charts.
- **Run history panel** pulling from `/results`.
- **Benchmark view** to trigger and visualise the multi-algorithm statistical comparison.

---

## 8. Progress So Far

RouteX has moved well past a single prototype script — it is a working, integrated, three-layer system:

- ✅ **Optimization core complete**: Greedy, GA, PSO, QPSO, and Hybrid QPSO+2-opt all implemented, sharing a common fitness/constraint/repair pipeline, with parameter tuning already done (particle counts, iteration counts, annealed β schedule — see the "TUNABLE SETTINGS" block in `main.py`).
- ✅ **Real road network integrated**: OSM extract of Kothrud, Pune loaded via OSMnx, converted into a routable NetworkX graph, with real shortest-path distances and GeoJSON route geometry served to the frontend.
- ✅ **Live traffic + incident simulation working**: TomTom-based live travel times, plus a repeatable "slow down this road → re-optimize" incident workflow, validated experimentally (`kothrud_alternative_corridor_slowdown`, verified with `incident_factor: 0.10`).
- ✅ **Rigorous benchmarking already performed**: multiple rounds of experiments across 6 scenarios (S1–S6) and 5 algorithms, with statistical summaries (mean, std-dev, min/max fitness, runtime) committed to the repo (`Testing_Evaluation/statistical_summary.csv`, `final_evaluation_summary.csv`) and rendered as comparison graphs (fitness stability, runtime, distance comparison charts in `Testing_Evaluation/graphs/`).
- ✅ **API fully documented and contract-tested**: `docs/API_CONTRACT.md` and `docs/graph_specification.md` define stable interfaces between the three subsystems, backed by an automated test suite (`tests/`, plus module-level tests under `backend/optimization/` and `traffic/`) covering graph loading, OSM parsing, API–traffic integration, and optimizer–traffic integration.
- ✅ **Working end-to-end dashboard**: the React app is not a mockup — it calls the live API, renders real routes on a map, and charts real convergence data.
- ✅ **Containerised for deployment**: a `Dockerfile` builds and serves the FastAPI backend (`uvicorn`) out of the box.

### Sample benchmark result (aggregate across evaluation scenarios)

| Algorithm | Avg. Fitness ↓ | Avg. Runtime (s) | Constraint Violations |
|---|---|---|---|
| **Hybrid QPSO + 2-opt** | **959.13** | 0.049 | 0 |
| Greedy VRP (baseline) | 978.69 | 0.0001 | 0 |
| GA | 1008.05 | 0.024 | 0 |
| QPSO | 1028.36 | 0.048 | 0 |
| PSO | 1039.46 | 0.027 | 0 |

*Lower fitness is better. The Hybrid QPSO+2-opt consistently produced the best or near-best solution quality across the tested scenarios (S1–S6) while remaining feasible (zero constraint violations) in every run — full per-scenario statistics are in `Testing_Evaluation/statistical_summary.csv`.*

---

## 9. Roadmap — What's Next

**Near-term (hackathon → post-hackathon polish)**
- [ ] Replace remaining hand-written test distance matrices with fully OSM-derived matrices for *every* scenario, not just Kothrud.
- [ ] Expand the OSM coverage area beyond Kothrud to a full city ward / metro region.
- [ ] Add authentication and multi-tenant scenario storage (today's SQLite store is single-instance).
- [ ] Surface fuel-cost and CO₂-emission estimates per route (fields already reserved in the API contract: `fuel_cost`, `congestion_penalty`).
- [ ] Automated CI pipeline running the existing `pytest` suite on every push.

**Medium-term (scaling the product)**
- [ ] Migrate persistence from SQLite to PostgreSQL/PostGIS for concurrent multi-user access and native geospatial queries.
- [ ] Move optimization runs to an async task queue (e.g. Celery/RQ) so large fleets (50+ vehicles, 200+ stops) don't block the API thread.
- [ ] Add horizontal scaling for the optimizer workers (containerised, stateless, behind a job queue) to handle enterprise-scale VRP instances.
- [ ] Support real-time GPS feed ingestion from vehicles for continuous re-optimization, not just simulated incidents.
- [ ] Multi-city support with pluggable OSM extracts selected at request time.
- [ ] Time-window constraints (VRPTW) and heterogeneous vehicle fleets (different capacities/speeds/costs).

**Longer-term / stretch features**
- [ ] Predictive traffic modelling (ML-based ETA forecasting) instead of relying solely on live/simulated factors.
- [ ] Driver-facing mobile app with turn-by-turn navigation synced to the optimized route.
- [ ] Multi-depot and dynamic customer insertion (new orders arriving mid-route).
- [ ] Pluggable objective functions (cost-minimising vs. emissions-minimising vs. SLA-priority routing) selectable per business.
- [ ] Public API/SDK so third-party logistics platforms can integrate RouteX as a routing-as-a-service backend.

---

## 10. Scaling Considerations

RouteX was designed from day one with a clean **traffic layer / optimization layer / API layer** separation specifically so it can scale independently at each layer:

- **Optimization layer** is stateless and takes a matrix in, returns routes out — it can be lifted into standalone worker processes/containers and scaled horizontally behind a queue without any API changes.
- **Traffic/graph layer** already caches loaded OSM graphs (`lru_cache`) and isolates all vendor-specific (TomTom) logic behind one module boundary — swapping or adding traffic providers, or pre-computing/caching matrices for popular regions, requires no changes elsewhere.
- **API layer** is a stateless FastAPI service — trivially replicable behind a load balancer; the only shared state (SQLite) is the intended first migration target (→ PostgreSQL) for concurrent multi-instance deployments.
- **Benchmark endpoint** already proves the system can run dozens of optimization jobs in a single request — the natural next step is exposing that as an async batch job for enterprise-scale scenario testing.
- The **Docker-first setup** (`Dockerfile`, `PORT` env-driven) means the backend is already container-orchestration-ready (Kubernetes/Cloud Run/ECS) with no rework.

---

## 11. Tech Stack

| Layer | Technology |
|---|---|
| Optimization | Python — custom QPSO / GA / PSO / Hybrid / Greedy implementations |
| Road network & traffic | OSMnx, NetworkX, TomTom Routing API |
| Backend API | FastAPI, Uvicorn, Pydantic, SQLite |
| Frontend | React 19, Vite, Leaflet + react-leaflet, Recharts, Axios |
| Testing | Pytest, httpx |
| Deployment | Docker |

---

## 12. Getting Started

### Backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# optional: enable live traffic
cp .env.example .env            # then add your TOMTOM_API_KEY

uvicorn backend.optimization.backend_ali.main:app --reload
```

The API will be live at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### Frontend

```bash
cd frontend/routex-dashboard
npm install
npm run dev
```

### Running the test suite

```bash
pip install -r requirements-dev.txt
pytest
```

### Running the full benchmark suite

```bash
python Testing_Evaluation/run_experiments.py
```

### Docker

```bash
docker build -t routex .
docker run -p 10000:10000 routex
```

---

## 13. Repository Structure

```
RouteX-main/
├── backend/optimization/          # Optimization algorithms (GA, PSO, QPSO, Hybrid, Greedy)
│   └── backend_ali/                # FastAPI app, SQLite persistence
├── traffic/                        # OSM loading, road-graph builder, live traffic client
├── data/raw/                       # Committed OSM extracts (Kothrud, larger area)
├── docs/                           # API contract + traffic-graph integration spec
├── frontend/routex-dashboard/      # React + Vite dashboard
├── tests/                          # Integration tests (API, graph, OSM loader)
├── Testing_Evaluation/             # Benchmark scripts, statistical analysis, result graphs
└── Dockerfile
```

---

## 14. Team

RouteX is built by a three-person team with clearly owned, contract-bound modules — enabling fully parallel development:

- **Optimization & algorithms** — QPSO, GA, PSO, Hybrid, fitness/constraints/repair
- **Traffic & road-network graph** — OSM loading, live traffic, incident simulation (`docs/graph_specification.md`)
- **Backend, database & frontend integration** — FastAPI, SQLite, API contract, React dashboard (`docs/API_CONTRACT.md`)

---
