import sqlite3
from pathlib import Path

DATABASE = Path(__file__).parent / "routex.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS optimization_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            algorithm TEXT NOT NULL,
            fitness REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Gradual schema upgrade (Stage 2) ---------------------------
    # Older databases only have (id, algorithm, fitness, created_at).
    # We add "distance" and "runtime" columns if they are missing, so
    # existing saved rows are kept and not deleted.
    cursor.execute("PRAGMA table_info(optimization_runs)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "distance" not in existing_columns:
        cursor.execute(
            "ALTER TABLE optimization_runs ADD COLUMN distance REAL"
        )

    if "runtime" not in existing_columns:
        cursor.execute(
            "ALTER TABLE optimization_runs ADD COLUMN runtime REAL"
        )

    if "scenario" not in existing_columns:
        cursor.execute(
            "ALTER TABLE optimization_runs ADD COLUMN scenario TEXT"
        )

    connection.commit()
    connection.close()


def save_result(algorithm, fitness_value, distance=None, runtime=None, scenario=None):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO optimization_runs (algorithm, fitness, distance, runtime, scenario)
        VALUES (?, ?, ?, ?, ?)
    """, (algorithm, fitness_value, distance, runtime, scenario))

    connection.commit()
    connection.close()


def get_results():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, algorithm, fitness, distance, runtime, scenario, created_at
        FROM optimization_runs
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    connection.close()

    results = []

    for row in rows:
        results.append({
            "id": row[0],
            "algorithm": row[1],
            "fitness": row[2],
            "distance": row[3],
            "runtime": row[4],
            "scenario": row[5],
            "created_at": row[6]
        })

    return results