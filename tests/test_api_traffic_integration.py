from fastapi.testclient import TestClient

from backend.optimization.backend_ali import database


def test_kothrud_api_saves_traffic_metrics_and_reoptimizes(tmp_path):
    # Keep API verification isolated from Ali's local development database.
    database.DATABASE = tmp_path / "routex-test.db"

    from backend.optimization.backend_ali.main import app

    client = TestClient(app)
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
    assert body["incident"]["leg"] == body["before"]["routes"][0][:2]

    saved = client.get(f"/results/{body['after_incident']['run_id']}")
    assert saved.status_code == 200
    assert saved.json()["travel_time"] == body["after_incident"]["travel_time"]
