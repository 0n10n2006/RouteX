# RouteX Optimization

This folder contains the optimization and benchmarking components for RouteX.

## Current Components

- `problem.py` — Defines the VRP problem instance.
- `qpso.py` — Quantum Particle Swarm Optimization implementation.
- `qpso_utils.py` — Random-key decoding and route generation.
- `local_search.py` — 2-opt local search.
- `hybrid.py` — Hybrid QPSO + 2-opt optimizer.
- `greedy_vrp.py` — Classical greedy VRP baseline.
- `dijkstra.py` — Dijkstra shortest-path algorithm.
- `constraints.py` — Route feasibility and capacity validation.
- `fitness.py` — Objective/fitness calculation.
- `result.py` — Common optimization result structure.
- `benchmark.py` — Single-scenario algorithm comparison.
- `experiment.py` — Repeated multi-scenario experiments.
- `scenarios.py` — Test scenario generation.
- `plot_convergence.py` — QPSO convergence visualization.

## Optimization Pipeline

```text
ProblemInstance
       |
       v
 Random-Key Position
       |
       v
 Customer Order
       |
       v
 Capacity-Aware Routes
       |
       v
 Constraint Validation
       |
       v
 Fitness Evaluation
       |
       v
 QPSO / Hybrid Optimization
       |
       v
 Best Routes + Fitness