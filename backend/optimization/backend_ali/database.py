"""SQLite storage for RouteX.

Owned by Ali (backend/database/integration).

Two tables:
  optimization_runs -> one row per algorithm run (the benchmark evidence)
  scenarios         -> the problems we can optimize (so they have stable IDs)

The schema grows GRADUALLY. create_tables() is safe to run every startup:
it creates anything missing and never drops or rewrites existing rows.
"""

import json
import sqlite3
from pathlib import Path

# Keep the DB next to this file so it works no matter where uvicorn is launched.
DATABASE = Path(__file__).parent / "routex.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    # row_factory lets us read columns by NAME instead of by position,
    # so adding a new column later can never shift/scramble existing reads.
    connection.row_factory = sqlite3.Row
    return connection


# --------------------------------------------------
# SMALL HELPERS
# --------------------------------------------------

def _dumps(value):
    """SQLite has no list/dict type, so store them as JSON text."""
    if value is None:
        return None
    return json.dumps(value)


def _loads(text, fallback):
    """Turn JSON text back into a Python list/dict; never crash on bad data."""
    if not text:
        return fallback
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return fallback

# --------------------------------------------------
# SCHEMA
# --------------------------------------------------

# Columns added to optimization_runs after the original 4.
# These names are fixed constants written by us (never user input),
# so building the ALTER statement from them is safe.
RUN_COLUMNS = {
    "distance": "REAL",
    "runtime": "REAL",
    "scenario": "TEXT",
    "routes": "TEXT",                  # JSON: [[0,1,2,0],[0,3,0]]
    "convergence": "TEXT",             # JSON: best fitness after each iteration
    "iterations": "INTEGER",
    "constraint_violations": "INTEGER",
    "vehicles_used": "INTEGER",
    "seed": "INTEGER",                 # random seed, so a run is reproducible
    # --- Not filled in yet: these need Zobiya's traffic model -------------
    # They stay NULL until travel_time = distance / effective_speed exists.
    "travel_time": "REAL",
    "congestion_penalty": "REAL",
    "fuel_cost": "REAL",
}


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # The original table (kept exactly as it was first created).
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS optimization_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT NOT NULL,
            fitness REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Gradual upgrade: add any column that does not exist yet.
    # Old rows are KEPT and simply show NULL for the new columns.
    cursor.execute("PRAGMA table_info(optimization_runs)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    for column, column_type in RUN_COLUMNS.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE optimization_runs ADD COLUMN {column} {column_type}"
            )

    # Scenarios get their own table so the frontend can refer to a stable id
    # instead of a hardcoded Python name.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            source TEXT,
            num_customers INTEGER,
            num_vehicles INTEGER,
            total_demand INTEGER,
            distance_matrix TEXT,
            vehicles TEXT,
            customers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

# --------------------------------------------------
# OPTIMIZATION RUNS
# --------------------------------------------------

def save_result(
    algorithm,
    fitness_value,
    distance=None,
    runtime=None,
    scenario=None,
    routes=None,
    convergence=None,
    iterations=None,
    constraint_violations=None,
    vehicles_used=None,
    seed=None,
    travel_time=None,
    congestion_penalty=None,
    fuel_cost=None,
):
    """Save one algorithm run. Returns the new row's id."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO optimization_runs (
            algorithm, fitness, distance, runtime, scenario,
            routes, convergence, iterations, constraint_violations,
            vehicles_used, seed, travel_time, congestion_penalty, fuel_cost
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        algorithm, fitness_value, distance, runtime, scenario,
        _dumps(routes), _dumps(convergence), iterations, constraint_violations,
        vehicles_used, seed, travel_time, congestion_penalty, fuel_cost
    ))

    run_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return run_id


def _row_to_run(row):
    """Turn a database row into a plain dict, decoding the JSON columns."""
    run = dict(row)
    run["routes"] = _loads(run.get("routes"), [])
    run["convergence"] = _loads(run.get("convergence"), [])
    return run


def get_results(limit=None):
    """All saved runs, newest first."""

    connection = get_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM optimization_runs ORDER BY id DESC"
    if limit:
        query += " LIMIT ?"
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)

    rows = cursor.fetchall()
    connection.close()

    return [_row_to_run(row) for row in rows]


def get_result(run_id):
    """One saved run by id, or None if it does not exist."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM optimization_runs WHERE id = ?",
        (run_id,)
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return _row_to_run(row)

# --------------------------------------------------
# SCENARIOS
# --------------------------------------------------

def save_scenario(
    name,
    distance_matrix,
    vehicles,
    customers,
    description=None,
    source="custom",
):
    """Insert a scenario, or update it if the name already exists.

    Idempotent on purpose: the built-in scenarios are registered on every
    startup and must not pile up duplicate rows."""

    total_demand = sum(customer.get("demand", 0) for customer in customers)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM scenarios WHERE name = ?", (name,))
    existing = cursor.fetchone()

    values = (
        description,
        source,
        len(customers),
        len(vehicles),
        total_demand,
        _dumps(distance_matrix),
        _dumps(vehicles),
        _dumps(customers),
    )

    if existing is None:
        cursor.execute("""
            INSERT INTO scenarios (
                name, description, source, num_customers, num_vehicles,
                total_demand, distance_matrix, vehicles, customers
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name,) + values)
        scenario_id = cursor.lastrowid
    else:
        cursor.execute("""
            UPDATE scenarios
            SET description = ?, source = ?, num_customers = ?, num_vehicles = ?,
                total_demand = ?, distance_matrix = ?, vehicles = ?, customers = ?
            WHERE name = ?
        """, values + (name,))
        scenario_id = existing["id"]

    connection.commit()
    connection.close()

    return scenario_id


def _row_to_scenario(row):
    scenario = dict(row)
    scenario["distance_matrix"] = _loads(scenario.get("distance_matrix"), [])
    scenario["vehicles"] = _loads(scenario.get("vehicles"), [])
    scenario["customers"] = _loads(scenario.get("customers"), [])
    return scenario


def get_scenarios():
    """All scenarios, in id order."""

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM scenarios ORDER BY id")
    rows = cursor.fetchall()
    connection.close()

    return [_row_to_scenario(row) for row in rows]


def get_scenario(scenario_id):
    """One scenario by numeric id, or None."""

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,))
    row = cursor.fetchone()
    connection.close()

    return None if row is None else _row_to_scenario(row)


def get_scenario_by_name(name):
    """One scenario by name, or None."""

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM scenarios WHERE name = ?", (name,))
    row = cursor.fetchone()
    connection.close()

    return None if row is None else _row_to_scenario(row)
