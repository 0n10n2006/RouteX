import sqlite3

DATABASE = "routex.db"


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

    connection.commit()
    connection.close()


def save_result(algorithm, fitness_value):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO optimization_runs (algorithm, fitness)
        VALUES (?, ?)
    """, (algorithm, fitness_value))

    connection.commit()
    connection.close()


def get_results():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, algorithm, fitness, created_at
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
            "created_at": row[3]
        })

    return results