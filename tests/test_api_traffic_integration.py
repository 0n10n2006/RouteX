from fastapi.testclient import TestClient
import pytest

from backend.optimization.backend_ali import database


def test_kothrud_api_saves_traffic_metrics_and_reoptimizes(tmp_path):
    # Keep API verification isolated from Ali's local development database.
    database.DATABASE = tmp_path / "routex-test.db"

    from backend.optimization.backend_ali.main import app

    client = TestClient(app)
    kothrud = client.get("/scenarios/kothrud")
    assert kothrud.status_code == 200
    assert len(kothrud.json()["travel_time_matrix"]) == 5

    response = client.post(
        "/optimize/kothrud-incident",
        json={
            "algorithm": "greedy",
            "seed": 42,
            "incident_factor": 0.25,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["before"]["scenario"] == "kothrud"
    assert body["before"]["distance"] is not None
    assert body["before"]["travel_time"] is not None
    assert body["after_incident"]["scenario"] == "kothrud_incident"
    assert body["after_incident"]["travel_time"] is not None
    assert body["incident"]["scenario"] == "kothrud_alternative_corridor_slowdown"
    assert body["traffic_metadata"]["after_incident"]["incident"] == body["incident"]

    saved = client.get(f"/results/{body['after_incident']['run_id']}")
    assert saved.status_code == 200
    assert saved.json()["travel_time"] == body["after_incident"]["travel_time"]

    geometry = client.get(f"/results/{body['after_incident']['run_id']}/geometry")
    assert geometry.status_code == 200
    assert geometry.json()["type"] == "FeatureCollection"
    assert len(geometry.json()["features"]) == body["after_incident"]["vehicles_used"]
    assert geometry.json()["features"][0]["geometry"]["type"] == "LineString"


def test_kothrud_incident_accepts_a_specific_osm_edge(tmp_path):
    database.DATABASE = tmp_path / "specific-edge-test.db"
    database.create_tables()

    from backend.optimization.backend_ali.main import app

    response = TestClient(app).post(
        "/optimize/kothrud-incident",
        json={
            "algorithm": "greedy",
            "seed": 77,
            "incident_edge": [1563310394, 4704828557, 0],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["incident"]["scenario"] == "custom_osm_edge"
    assert body["incident"]["edge"] == [1563310394, 4704828557, 0]
    assert body["before"]["seed"] == body["after_incident"]["seed"] == 77


def test_custom_scenario_accepts_and_uses_travel_time_matrix(tmp_path):
    database.DATABASE = tmp_path / "custom-scenario-test.db"
    database.create_tables()

    from backend.optimization.backend_ali.main import app

    client = TestClient(app)
    payload = {
        "name": "travel-time-api-test",
        "description": "Custom matrix supplied through the API",
        "distance_matrix": [[0, 5, 9], [5, 0, 4], [9, 4, 0]],
        "travel_time_matrix": [[0, 50, 20], [50, 0, 40], [20, 40, 0]],
        "vehicles": [{"id": 1, "capacity": 10}],
        "customers": [{"id": 1, "demand": 2}, {"id": 2, "demand": 2}],
    }

    created = client.post("/scenarios", json=payload)
    assert created.status_code == 200
    assert created.json()["scenario"]["travel_time_matrix"] == payload["travel_time_matrix"]

    optimized = client.post(
        "/optimize",
        json={"algorithm": "greedy", "scenario": payload["name"]},
    )
    assert optimized.status_code == 200
    assert optimized.json()["travel_time"] == 110.0


@pytest.mark.parametrize(
    ("algorithm", "display_name"),
    [("ga", "GA"), ("pso", "PSO")],
)
def test_kothrud_api_runs_classical_metaheuristics(tmp_path, algorithm, display_name):
    database.DATABASE = tmp_path / f"{algorithm}-api-test.db"
    database.create_tables()

    from backend.optimization.backend_ali.main import app

    response = TestClient(app).post(
        "/optimize",
        json={"algorithm": algorithm, "scenario": "kothrud", "seed": 42},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == display_name
    assert body["travel_time"] is not None
    assert body["feasible"] is True


def test_optimize_rejects_unknown_algorithm(tmp_path):
    database.DATABASE = tmp_path / "unknown-algorithm-test.db"
    database.create_tables()

    from backend.optimization.backend_ali.main import app

    response = TestClient(app).post(
        "/optimize",
        json={"algorithm": "not-an-algorithm", "scenario": "kothrud"},
    )
    assert response.status_code == 400


def test_benchmark_runs_ga_and_pso_and_rejects_unknown_algorithms(tmp_path):
    database.DATABASE = tmp_path / "benchmark-algorithm-test.db"
    database.create_tables()

    from backend.optimization.backend_ali.main import app

    client = TestClient(app)
    benchmark = client.post(
        "/benchmark",
        json={
            "seeds": 1,
            "scenarios": ["kothrud"],
            "algorithms": ["ga", "pso"],
        },
    )
    assert benchmark.status_code == 200
    assert {run["algorithm"] for run in benchmark.json()["runs"]} == {"GA", "PSO"}

    invalid = client.post("/benchmark", json={"algorithms": ["unknown"]})
    assert invalid.status_code == 400
