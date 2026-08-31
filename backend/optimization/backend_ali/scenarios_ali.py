"""
Extra, harder scenarios owned by Ali (backend/integration).

Why this file exists:
- The team's scenarios.py (low/medium/high) all share the SAME small 5-node
  road map and only change customer demand. On that tiny problem QPSO already
  finds the optimum, so every algorithm ties and the benchmark looks flat.
- This file adds a BIGGER problem (depot + 6 customers) with capacity that
  forces multiple vehicles. That gives QPSO real room to beat Greedy and gives
  Hybrid's 2-opt something to improve — a much stronger demo.

It lives in backend_ali/ so it is Ali's own code and does not modify any
teammate's file. main.py merges these on top of create_scenarios().
"""

# Same import pattern as main.py: relative when imported by the API package,
# flat when run directly from inside optimization/.
try:
    from ..problem import ProblemInstance
except ImportError:  # pragma: no cover - only hit on direct execution
    from problem import ProblemInstance


def create_extra_scenarios():

    # 7x7 symmetric distance matrix: node 0 is the depot, nodes 1..6 are
    # customers. Distances are made up but consistent (matrix[i][j] == matrix[j][i]).
    distance_matrix = [
        [0,  12, 18, 22, 30, 25, 14],
        [12,  0, 10, 16, 28, 20, 11],
        [18, 10,  0,  9, 19, 15, 13],
        [22, 16,  9,  0, 12, 18, 20],
        [30, 28, 19, 12,  0, 10, 24],
        [25, 20, 15, 18, 10,  0, 16],
        [14, 11, 13, 20, 24, 16,  0],
    ]

    # 3 vehicles, capacity 10 each (total capacity 30).
    vehicles = [
        {"id": 1, "capacity": 10},
        {"id": 2, "capacity": 10},
        {"id": 3, "capacity": 10},
    ]

    # 6 customers, total demand 21 -> needs at least 3 vehicles (capacity binds).
    customers = [
        {"id": 1, "demand": 3},
        {"id": 2, "demand": 4},
        {"id": 3, "demand": 2},
        {"id": 4, "demand": 5},
        {"id": 5, "demand": 3},
        {"id": 6, "demand": 4},
    ]

    big = ProblemInstance(
        distance_matrix=distance_matrix,
        vehicles=vehicles,
        customers=customers,
    )

    return {"big": big}


if __name__ == "__main__":

    for name, problem in create_extra_scenarios().items():
        print(name, "scenario:", len(problem.customers), "customers,",
              len(problem.vehicles), "vehicles")
