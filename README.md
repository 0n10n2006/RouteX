
# 🚚 RouteX
### Quantum-Inspired, Traffic-Aware Vehicle Routing Optimization

*Smarter last-mile delivery routes using a Hybrid Quantum-behaved Particle Swarm Optimizer, real road networks, and live traffic — benchmarked, tested, and visualized end-to-end.*

---

## 1. The Problem We're Solving

Last-mile delivery and fleet routing is one of the most expensive parts of logistics — inefficient routes waste fuel, driver hours, and money, and get worse the moment real-world traffic and road incidents are added to the picture. Classical routing heuristics (nearest-neighbour, greedy assignment) are fast but shallow: they converge quickly to mediocre routes and don't adapt when the road network changes underneath them.

**RouteX** is a full-stack Vehicle Routing Problem (VRP) optimization platform that:

- Solves multi-vehicle, capacity-constrained routing with a **Hybrid Quantum-behaved Particle Swarm Optimization (QPSO)** algorithm — combining global swarm search with 2-opt, Or-opt, and iterated local search refinement — benchmarked against Genetic Algorithms, classical PSO, and a Greedy baseline.
- Runs on **real road geometry** (OpenStreetMap extracts for Kothrud and a larger area of Pune) instead of toy distance matrices — routes actually follow streets, with real travel-time costs.
- Reacts to **live traffic conditions** (TomTom Traffic API) and **simulated or detected road incidents**, re-optimizing affected routes automatically instead of treating routing as a one-time calculation.
- Lets users build **custom scenarios anywhere in the world** — click to place multiple depots and customers on a live map, pick which depot is active, configure a fleet, and run the optimizer against real OSM road data for that location.
- Ships with **Firebase-authenticated accounts**, **per-user saved depots**, and a **role-gated admin view**, on top of the optimization engine itself.
- Exposes everything through a documented **FastAPI backend + SQLite persistence layer**, and a **React + Leaflet + Recharts dashboard** for visual, judge-friendly demos.

---

## 2. What Makes RouteX Different

| # | Feature | Why it matters |
|---|---|---|
| 1 | **Hybrid QPSO + 2-opt + Or-opt + iterated local search** | QPSO performs global search with an *annealed* beta coefficient (explore early, exploit late). Whenever it finds a new global best, local search runs on the top-K particles — combining 2-opt (segment reversal) with Or-opt (relocating 1–3 customers within or *across* vehicle routes) and double-bridge perturbation kicks, so the optimizer can escape local optima that plain 2-opt gets permanently stuck in. |
| 2 | **Five algorithms benchmarked head-to-head in one platform** | Greedy, GA, PSO, QPSO, and the Hybrid all run against identical scenarios and seeds, so the improvement of the hybrid approach is *measured*, not claimed. |
| 3 | **Real road-network routing, not a toy matrix** | Uses OSMnx + NetworkX to load real OSM extracts (Kothrud and a larger 6.5 km × 6.2 km area of Pune), compute real shortest-path road distances and travel times, and render true polyline routes on a Leaflet map. |
| 4 | **Live traffic + incident-aware re-optimization** | Integrates the TomTom Traffic API for traffic-adjusted travel times, and can simulate or detect a road slowdown/closure on an already-optimized route, then automatically re-optimize the affected routes. |
| 5 | **Custom scenarios anywhere, with multiple depots** | The Scenario Builder isn't limited to the two pre-built Pune extracts — click anywhere on the map to place depots and customers, download real road data for that location on demand, and place several depot candidates while choosing which one is active per run. |
| 6 | **Reproducible, seeded experimentation** | Every run accepts an optional seed; the same scenario + algorithm + seed always reproduces the same result — essential for fair benchmarking and for judges to verify claims live. |
| 7 | **Built-in statistical benchmarking endpoint** | `POST /benchmark` runs every algorithm × scenario × seed combination in one call and returns mean/best/worst fitness, runtime, and % improvement over the greedy baseline — no manual spreadsheet work needed. |
| 8 | **Full observability, not a black box** | Every run persists its convergence curve, constraint-violation count, vehicles used, distance, and travel time to SQLite and exposes them via REST — the dashboard charts *how* the algorithm converged, not just the final number. |
| 9 | **Accounts, saved depots, and an admin view** | Firebase-authenticated login, per-user permanent depots you can save and reload across sessions, and a role-gated admin dashboard for monitoring usage. |
| 10 | **Clean separation of concerns** | Traffic/graph layer, optimization layer, and API/persistence layer are independent modules with a written contract (`docs/graph_specification.md`, `docs/API_CONTRACT.md`) — built by a 3-person team working in parallel without blocking each other. |

---

## 3. How It Works — The Pipeline

```
Real-World Data  →  Graph Model  →  Hybrid QPSO  →  2-opt / Or-opt  →  Feasibility Check  →  Optimized Routes
(OSM roads,         (road network    (global search,   (local          (repair &            (feasible,
 vehicles, live       as nodes         multiple          refinement)      validate             traffic-aware,
 traffic)             & edges)         routes)                            constraints)          ready to deploy)
                                                                                ↑                       │
                                                                                └── re-optimize ─────────┘
                                                                          (triggered on traffic/incident change)
```

Every stage re-runs automatically the moment traffic conditions or incidents change — routing isn't a one-time calculation.

---

## 4. Optimization Engine Details

### 4.1 Algorithms benchmarked

| Algorithm | Description |
|---|---|
| **Greedy** | Nearest-neighbour baseline. Fast, no learning, used as the floor to measure improvement against. |
| **GA** | Genetic Algorithm with order-preserving crossover and mutation. |
| **PSO** | Classical Particle Swarm Optimization over a random-key encoding. |
| **QPSO** | Quantum-behaved PSO — samples particle positions from a quantum potential well instead of classical velocity updates, giving better global exploration. |
| **Hybrid QPSO** | QPSO for global search + local search refinement for exploitation. This is RouteX's primary algorithm. |

### 4.2 The Hybrid, in detail

1. **QPSO global search** runs with an **annealed beta** — starting high (more exploration) and linearly decaying toward a floor (more exploitation) over the run, instead of a fixed exploration rate for the whole search.
2. Whenever QPSO discovers a new global best, **local search runs on the top-K particles** (not just the single best), each starting from a different point in the search space.
3. Local search itself is an alternating **2-opt + Or-opt descent**:
   - **2-opt** reverses a segment within a single route to remove crossing paths.
   - **Or-opt** relocates 1–3 consecutive customers — within a route *or across vehicles* — which is the only move that can fix a bad initial route partition. This is what lets the hybrid escape local optima that 2-opt alone gets permanently stuck in.
4. If local search stalls, a **double-bridge perturbation** ("kick") restructures the route and the descent runs again — this is standard **Iterated Local Search (ILS)**, and it can never return a worse solution than plain 2-opt.
5. Every candidate solution is **repaired and validated** (`constraints.py`) against vehicle capacity, depot start/end, and full customer coverage *before* it's scored, so infeasible solutions never dominate the search.

### 4.3 Benchmark results (real numbers, not marketing)

On the `larger_area` real-OSM Pune scenario (8 customers, 3 vehicles, real road distances with simulated traffic slowdowns), across 5 seeds:

| Metric | Result |
|---|---|
| Hybrid vs. Greedy baseline | **~18% faster** total fleet travel time |
| Hybrid vs. GA | **Wins or ties on 5 / 5 seeds** (previously lost on some before the Or-opt/ILS/annealing upgrade) |
| Typical run time (8 customers, 3 vehicles) | **< 0.1 seconds** |
| Algorithms compared head-to-head | Greedy, GA, PSO, QPSO, Hybrid QPSO |

Run `POST /benchmark` yourself, or see `Testing_Evaluation/` for the full CSV output and convergence plots this table is drawn from.

---

## 5. Frontend

Built with React + Vite, Leaflet (via `react-leaflet`), and Recharts, styled with a custom dark navy/cyan theme (no generic UI-kit look-and-feel).

| View | What it does |
|---|---|
| **Landing / Login** | Firebase email/password auth, plus a "View Demo" option that skips login entirely for quick judging. |
| **Dashboard** | KPI overview of recent runs. |
| **Scenario Builder** | Click anywhere on a live map to place depots and customers; place multiple depots and choose which is active; configure a custom vehicle fleet; run any algorithm against real OSM road data downloaded on demand for that location. |
| **Optimization** | Run built-in scenarios (Kothrud, larger area, synthetic sizes) against any algorithm, with the resulting route rendered on a real road-geometry map. |
| **Comparison** | Side-by-side algorithm comparison charts. |
| **Run History** | Every past run, persisted and queryable. |
| **Admin** | Role-gated view of registered users and activity (Firebase-authenticated). |

The Optimization and Scenario Builder maps use standard OpenStreetMap tiles (always free, no API key) with a CSS filter for the dark look, rather than depending on a third-party "dark mode" tile provider's free-tier policy.

---

## 6. System Architecture

```
routex/
├── backend/
│   └── optimization/
│       ├── qpso.py, pso.py, ga.py, greedy_vrp.py   # the five algorithms
│       ├── hybrid.py                                # Hybrid QPSO orchestration
│       ├── local_search.py                          # 2-opt, Or-opt, ILS, double-bridge
│       ├── fitness.py, constraints.py, repair.py     # scoring & feasibility
│       ├── problem.py                                # VRP problem representation
│       ├── traffic_scenarios.py, scenarios.py        # built-in scenarios
│       ├── benchmark.py                              # statistical benchmarking
│       └── backend_ali/
│           ├── main.py                               # FastAPI app & all endpoints
│           └── database.py                           # SQLite persistence
├── traffic/
│   ├── graph_builder.py                              # OSM graph -> distance/time matrix
│   ├── osm_loader.py                                 # loads/prepares OSM extracts
│   └── live_traffic.py                               # TomTom Traffic API integration
├── data/raw/                                         # OSM extracts (Kothrud, larger area)
├── frontend/routex-dashboard/                        # React + Vite dashboard (see §5)
├── docs/                                              # API_CONTRACT.md, graph_specification.md
└── Testing_Evaluation/                                # benchmark CSVs & convergence plots
```

---

## 7. API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/optimize` | Run a built-in scenario against a chosen algorithm |
| `POST` | `/optimize/custom` | Run the optimizer against user-defined locations/vehicles (Scenario Builder) |
| `POST` | `/optimize/kothrud-incident` | Simulate a traffic incident on Kothrud and re-optimize |
| `GET` | `/results`, `/results/{run_id}` | Fetch past run results |
| `GET` | `/results/{run_id}/geometry` | Real road-geometry polylines for map rendering |
| `GET` | `/results/{run_id}/convergence` | Convergence curve for charting |
| `GET` | `/scenarios`, `POST /scenarios` | List / create scenarios |
| `POST` | `/benchmark` | Run every algorithm × scenario × seed combination and return statistics |
| `POST` | `/auth/sync`, `GET /auth/me` | Firebase-authenticated account sync |
| `GET` | `/admin/users` | Role-gated admin view |
| `GET/POST/DELETE` | `/depots` | Per-user saved depot locations |

Full request/response shapes are in `docs/API_CONTRACT.md`.

---

## 8. Getting Started

### 8.1 Backend

```bash
python -m venv venv
./venv/Scripts/Activate      # Windows PowerShell
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional: for tests + convergence plots

cp .env.example .env
# edit .env and set TOMTOM_API_KEY (only needed for live traffic features)

python -m uvicorn backend.optimization.backend_ali.main:app --reload
```

> **Note:** always create a fresh `venv` inside the project folder you're actually running from — Windows venvs aren't relocatable, and copying a `venv` folder from another location will silently install packages into the wrong environment.

Firebase auth verification needs no service-account file — it only verifies ID tokens against the public project ID (`routex-auth`), configured directly in `main.py`.

### 8.2 Frontend

```bash
cd frontend/routex-dashboard
npm install
npm run dev
```

Open the printed local URL. The dashboard talks to the backend at `http://127.0.0.1:8000` by default.

### 8.3 Running tests

```bash
pytest
```

---

## 9. Roadmap

**Near-term**
- Or-opt segment length tuning per scenario size
- Persisted incident history, not just simulated single-shot incidents

**Medium-term**
- Multi-depot *optimization* (not just multi-depot placement) — genuinely assigning vehicles to whichever depot minimizes total cost, rather than one active depot per run
- Real-time WebSocket push of re-optimized routes instead of polling

**Stretch**
- Time-window constraints (deliveries due within a time slot)
- Multi-day route planning

**Scaling**
- The optimization core is stateless per request — horizontally scaling the FastAPI layer behind a load balancer requires no changes to `backend/optimization/`
- SQLite is sufficient for demo/hackathon scale; a swap to Postgres would only touch `database.py`

---

## 10. Team

Built for **Smart India Hackathon 2026** by a 3-person team working across the traffic/graph layer, the optimization engine, and the backend/frontend integration.
